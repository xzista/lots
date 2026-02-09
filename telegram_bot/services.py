import asyncio
import html

from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from asgiref.sync import sync_to_async
from django.conf import settings
from redis.asyncio import Redis
from .models import TelegramDialog, TelegramMessage
from lots.models import Lot
from redis.exceptions import LockError

# инициализация клиента Redis
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


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


# ---------- REDIS HELPERS ----------

async def get_cached_topic_id(user_id):
    """Получить ID топика из кэша Redis"""
    return await redis_client.get(f"topic_id:{user_id}")


async def set_cached_topic_id(user_id, topic_id):
    """Сохранить ID топика в кэш на 24 часа"""
    await redis_client.set(f"topic_id:{user_id}", topic_id, ex=86400)


async def delete_cached_topic_id(user_id):
    """Удалить ID топика из кэша"""
    await redis_client.delete(f"topic_id:{user_id}")


# ---------- BOT LOGIC ----------

async def handle_start(message: types.Message):
    payload = message.text.replace("/start", "").strip()
    dialog, _ = await get_or_create_dialog(message.from_user)

    if payload.startswith("lot_"):
        lot_id = payload.replace("lot_", "")
        lot = await get_lot_safe(lot_id)
        if lot:
            await set_dialog_lot(dialog.id, lot)
            await message.answer(f"🖼 Предмет: {lot.title}\n\nНапишите ваш вопрос:")
            return

    await set_dialog_lot(dialog.id, None)
    await message.answer("Здравствуйте! Напишите ваш вопрос.")


async def handle_message(message: types.Message):
    user_id = message.from_user.id
    try:
        async with redis_client.lock(f"lock:topic_creation:{user_id}", timeout=30, blocking_timeout=5):
            # сначала ищем ID топика в кэше
            topic_id = await get_cached_topic_id(user_id)
            dialog, _ = await get_or_create_dialog(message.from_user)

            is_new_topic_needed = False

            # если в кэше нет, берем из БД
            if not topic_id:
                topic_id = dialog.topic_id

            if topic_id:
                try:
                    # проверяем, жив ли топик в Telegram (вызываем typing)
                    await message.bot.send_chat_action(
                        chat_id=settings.TG_ADMIN_GROUP_ID,
                        action="typing",
                        message_thread_id=int(topic_id)
                    )
                    # если успешно значит обновляем кэш, чтобы не дергать БД в следующий раз
                    await set_cached_topic_id(user_id, topic_id)
                except Exception:
                    # если ошибка (топик удален вручную в ТГ), создаем новый
                    is_new_topic_needed = True
            else:
                is_new_topic_needed = True

            if is_new_topic_needed:
                try:
                    topic_name = f"{dialog.first_name or ''} @{dialog.username or ''}"[:128]
                    topic = await message.bot.create_forum_topic(
                        chat_id=settings.TG_ADMIN_GROUP_ID,
                        name=topic_name
                    )
                    topic_id = topic.message_thread_id
                    await update_dialog_topic(dialog.id, topic_id)
                    await set_cached_topic_id(user_id, topic_id)
                except Exception as e:
                    return await message.answer("Ошибка связи с администратором. Попробуйте позже.")
    except LockError:
        return await message.answer("Ваше сообщение обрабатывается, пожалуйста, подождите...")

    # сохранение сообщения в БД
    await create_msg(dialog, message.text, is_from_user=True)

    # сообщения для админа
    base_url = settings.CSRF_TRUSTED_ORIGINS[0].rstrip('/')
    safe_name = html.escape(dialog.first_name or "Пользователь")
    safe_username = html.escape(dialog.username or "")
    safe_text = html.escape(message.text or "")
    lot_info = ""
    if dialog.current_lot:
        lot_url = f"{base_url}/{dialog.current_lot.id}/"
        safe_lot_title = html.escape(dialog.current_lot.title)
        lot_info = f'🖼 Предмет: <a href="{lot_url}">{safe_lot_title}</a> - {dialog.current_lot.price}₽\n'

    text = (
        f"🧑 <b>{safe_name}</b> @{safe_username}\n"
        f"ID: <code>{dialog.tg_user_id}</code>\n{lot_info}\n💬 {safe_text}"
    )

    reply_markup = None
    if is_new_topic_needed:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(
            text="✅ Завершить диалог",
            callback_data=f"close_topic_{user_id}")
        )
        reply_markup = builder.as_markup()

    await message.bot.send_message(
        chat_id=settings.TG_ADMIN_GROUP_ID,
        message_thread_id=int(topic_id),
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
        disable_web_page_preview=False
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
        await message.bot.send_message(dialog.tg_user_id, message.text, parse_mode="HTML")
    except TelegramDialog.DoesNotExist:
        try:
            await message.bot.send_message(dialog.tg_user_id, message.text)
        except:
            pass


async def handle_close_topic(callback: types.CallbackQuery):
    user_id = callback.data.replace("close_topic_", "")
    try:
        dialog = await get_dialog_with_lot(user_id)
        if dialog and dialog.topic_id:
            try:
                await callback.bot.delete_forum_topic(
                    chat_id=settings.TG_ADMIN_GROUP_ID,
                    message_thread_id=dialog.topic_id
                )
            except Exception:
                pass

            # очистка кэша в Redis и обнуление id топика в БД
            await delete_cached_topic_id(user_id)
            await update_dialog_topic(dialog.id, None)

        await callback.answer("Диалог закрыт, топик удален", show_alert=True)
    except Exception:
        await callback.answer("Ошибка при закрытии")