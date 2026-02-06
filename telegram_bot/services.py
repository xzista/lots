from asgiref.sync import sync_to_async
from django.conf import settings
from .models import TelegramDialog, TelegramMessage
from lots.models import Lot


# ---------- ORM helpers ----------

@sync_to_async
def get_or_create_dialog(user):
    return TelegramDialog.objects.get_or_create(
        tg_user_id=user.id,
        defaults={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )


@sync_to_async
def get_dialog_by_user_id(tg_user_id):
    return TelegramDialog.objects.get(tg_user_id=tg_user_id)


@sync_to_async
def get_lot(lot_id):
    return Lot.objects.get(id=lot_id)


@sync_to_async
def save_dialog(dialog):
    dialog.save()


@sync_to_async
def create_user_message(dialog, text):
    return TelegramMessage.objects.create(
        dialog=dialog,
        text=text,
        is_from_user=True
    )


@sync_to_async
def create_admin_message(dialog, text):
    return TelegramMessage.objects.create(
        dialog=dialog,
        text=text,
        is_from_user=False
    )


# ---------- Bot logic ----------

async def handle_start(message):
    payload = message.text.replace("/start", "").strip()

    dialog, _ = await get_or_create_dialog(message.from_user)

    if payload.startswith("lot_"):
        lot_id = payload.replace("lot_", "")
        try:
            lot = await get_lot(lot_id)
            dialog.current_lot = lot
            await save_dialog(dialog)

            await message.answer(
                f"🖼️ Лот: {lot.title}\n\nНапишите ваше сообщение:"
            )
        except Lot.DoesNotExist:
            await message.answer("Лот не найден")
    else:
        dialog.current_lot = None
        await save_dialog(dialog)
        await message.answer("Здравствуйте! Напишите ваш вопрос.")


async def handle_message(message):
    dialog = await get_dialog_by_user_id(message.from_user.id)

    await create_user_message(dialog, message.text)

    text = (
        f"🧑 {dialog.first_name or ''} @{dialog.username or ''}\n"
        f"ID: {dialog.tg_user_id}\n"
    )

    if dialog.current_lot:
        text += f"🖼️ Предмет: {dialog.current_lot.title}\n"

    text += f"\n💬 {message.text}"

    await message.bot.send_message(settings.TG_ADMIN_ID, text)
    await message.answer("Сообщение отправлено 👍")


async def handle_admin_reply(message):
    if message.from_user.id != settings.TG_ADMIN_ID:
        return

    lines = message.reply_to_message.text.splitlines()
    user_id = None

    for line in lines:
        if line.startswith("ID:"):
            user_id = int(line.replace("ID:", "").strip())

    if not user_id:
        return

    dialog = await get_dialog_by_user_id(user_id)

    await create_admin_message(dialog, message.text)

    await message.bot.send_message(user_id, message.text)