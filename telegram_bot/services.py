import asyncio
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from django.conf import settings
from .models import TelegramDialog, TelegramMessage
from lots.models import Lot


# ---------- ORM helpers ----------

@sync_to_async
def get_or_create_dialog(user):
    dialog, created = TelegramDialog.objects.select_related('current_lot').get_or_create(
        tg_user_id=user.id,
        defaults={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )
    return dialog, created


@sync_to_async
def get_dialog_with_lot(user_id):
    return TelegramDialog.objects.select_related('current_lot').filter(tg_user_id=user_id).first()


@sync_to_async
def update_dialog_topic(dialog_id, topic_id):
    TelegramDialog.objects.filter(id=dialog_id).update(topic_id=topic_id)


@sync_to_async
def set_dialog_lot(dialog_id, lot_obj):
    TelegramDialog.objects.filter(id=dialog_id).update(current_lot=lot_obj)


@sync_to_async
def create_msg(dialog, text, is_from_user):
    return TelegramMessage.objects.create(dialog=dialog, text=text, is_from_user=is_from_user)


@sync_to_async
def get_lot_safe(lot_id):
    try:
        return Lot.objects.filter(id=int(lot_id)).first()
    except (ValueError, TypeError):
        return None


# ---------- BOT LOGIC ----------

async def handle_start(message: types.Message):
    payload = message.text.replace("/start", "").strip()
    dialog, _ = await get_or_create_dialog(message.from_user)

    if payload.startswith("lot_"):
        lot_id = payload.replace("lot_", "")
        lot = await get_lot_safe(lot_id)
        if lot:
            await set_dialog_lot(dialog.id, lot)
            await message.answer(f"🖼 Лот: {lot.title}\n\nНапишите ваш вопрос:")
            return

    await set_dialog_lot(dialog.id, None)
    await message.answer("Здравствуйте! Напишите ваш вопрос.")


topic_lock = asyncio.Lock()


async def handle_message(message: types.Message):
    # 1. Получаем/создаем диалог
    dialog, _ = await get_or_create_dialog(message.from_user)

    # 2. Проверяем актуальность топика под локом
    is_new_topic_needed = False
    async with topic_lock:
        # Важно: перечитываем dialog из БД, если он мог быть изменен другим процессом
        dialog = await get_dialog_with_lot(message.from_user.id)

        if dialog.topic_id:
            try:
                # Проверяем, жив ли топик в Telegram
                await message.bot.send_chat_action(
                    chat_id=settings.TG_ADMIN_GROUP_ID,
                    action="typing",
                    message_thread_id=dialog.topic_id
                )
            except Exception:
                # Если ошибка (топик удален), помечаем на создание нового
                is_new_topic_needed = True
        else:
            is_new_topic_needed = True

        if is_new_topic_needed:
            try:
                topic = await message.bot.create_forum_topic(
                    chat_id=settings.TG_ADMIN_GROUP_ID,
                    name=f"{dialog.first_name or ''} @{dialog.username or ''}"[:128]
                )
                dialog.topic_id = topic.message_thread_id
                await update_dialog_topic(dialog.id, dialog.topic_id)
            except Exception as e:
                return await message.answer("Ошибка связи с администратором. Попробуйте позже.")

    # 3. Сохраняем сообщение в БД (оно всегда привязано к одному dialog)
    await create_msg(dialog, message.text, is_from_user=True)

    # 4. Отправка в админ-группу
    lot_info = f"🖼 Лот: {dialog.current_lot.title}\n" if dialog.current_lot else ""
    text = (
        f"🧑 {dialog.first_name or ''} @{dialog.username or ''}\n"
        f"ID: {dialog.tg_user_id}\n{lot_info}💬 {message.text}"
    )

    if is_new_topic_needed:
        # Если создали новый топик — добавляем кнопку закрытия
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(
            text="✅ Завершить диалог",
            callback_data=f"close_topic_{dialog.tg_user_id}")
        )
        await message.bot.send_message(
            chat_id=settings.TG_ADMIN_GROUP_ID,
            message_thread_id=dialog.topic_id,
            text=text,
            reply_markup=builder.as_markup()
        )
    else:
        # Просто пересылаем сообщение в существующий топик
        await message.bot.send_message(
            chat_id=settings.TG_ADMIN_GROUP_ID,
            message_thread_id=dialog.topic_id,
            text=text
        )

    await message.answer("Сообщение передано администратору 👍")


async def handle_admin_reply(message: types.Message):
    if message.chat.id != settings.TG_ADMIN_GROUP_ID or message.from_user.is_bot:
        return
    if not message.message_thread_id or message.message_thread_id == 1:
        return

    try:
        dialog = await sync_to_async(TelegramDialog.objects.get)(topic_id=message.message_thread_id)
        await create_msg(dialog, message.text, is_from_user=False)
        await message.bot.send_message(dialog.tg_user_id, message.text)
    except TelegramDialog.DoesNotExist:
        pass


async def handle_close_topic(callback: types.CallbackQuery):
    user_id = callback.data.replace("close_topic_", "")
    try:
        dialog = await get_dialog_with_lot(user_id)
        if dialog and dialog.topic_id:
            # 1. Удаляем визуально из Telegram
            try:
                await callback.bot.delete_forum_topic(
                    chat_id=settings.TG_ADMIN_GROUP_ID,
                    message_thread_id=dialog.topic_id
                )
            except Exception:
                pass

                # 2. Обнуляем в БД. История сообщений в TelegramMessage НЕ УДАЛЯЕТСЯ.
            await update_dialog_topic(dialog.id, None)

        await callback.answer("Диалог закрыт, топик удален", show_alert=True)
    except Exception:
        await callback.answer("Ошибка при закрытии")