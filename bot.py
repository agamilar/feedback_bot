import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message

from config import ADMIN_CHAT_ID, BOT_TOKEN
from database import get_user_for_admin_message, init_db, save_mapping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


def is_admin_chat(message: Message) -> bool:
    return message.chat.id == ADMIN_CHAT_ID


# ---------------------------------------------------------------------------
# User side: any private message NOT coming from the admin chat
# ---------------------------------------------------------------------------

@router.message(Command("start"), ~F.chat.id.in_({ADMIN_CHAT_ID}))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Напишите сюда ваш вопрос или сообщение — "
        "оно будет передано в поддержку, и вам ответят прямо здесь."
    )


@router.message(~F.chat.id.in_({ADMIN_CHAT_ID}))
async def handle_user_message(message: Message, bot: Bot) -> None:
    """Forward any message from a user to the admin chat and remember the link."""
    try:
        forwarded = await bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
    except Exception:
        logger.exception("Failed to forward message from user %s", message.from_user.id)
        await message.answer("Не удалось отправить сообщение, попробуйте ещё раз позже.")
        return

    save_mapping(
        admin_message_id=forwarded.message_id,
        user_id=message.chat.id,
        user_message_id=message.message_id,
    )

    # Small extra context line under the forward, so the admin knows who it's from
    user = message.from_user
    name = user.full_name if user else "Unknown"
    username = f"@{user.username}" if user and user.username else f"id{message.chat.id}"
    await bot.send_message(
        ADMIN_CHAT_ID,
        f"⬆️ От: {name} ({username})",
        reply_to_message_id=forwarded.message_id,
    )

    await message.answer("Спасибо! Ваше сообщение передано в поддержку.")


# ---------------------------------------------------------------------------
# Admin side: replies inside the admin chat get routed back to the user
# ---------------------------------------------------------------------------

@router.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def handle_admin_reply(message: Message, bot: Bot) -> None:
    replied = message.reply_to_message

    # The admin might reply either to the forwarded message itself, or to the
    # "От: Name (@username)" context line sent right after it (id = forwarded_id + 1).
    user_id = get_user_for_admin_message(replied.message_id)
    if user_id is None:
        user_id = get_user_for_admin_message(replied.message_id - 1)

    if user_id is None:
        await message.reply(
            "Не нашёл, кому отправить ответ — похоже, это не пересланное сообщение."
        )
        return

    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=ADMIN_CHAT_ID,
            message_id=message.message_id,
        )
    except Exception:
        logger.exception("Failed to deliver admin reply to user %s", user_id)
        await message.reply("Не удалось доставить ответ пользователю (возможно, бот заблокирован).")
        return

    await message.reply("✅ Отправлено")


@router.message(F.chat.id == ADMIN_CHAT_ID)
async def handle_admin_stray_message(message: Message) -> None:
    """Admin wrote in the chat without replying to a forwarded message."""
    await message.reply(
        "Чтобы ответить пользователю, отправьте ответ (Reply) на его пересланное сообщение."
    )


async def main() -> None:
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
