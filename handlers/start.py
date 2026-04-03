# handlers/start.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db import register_user, get_user_by_telegram

router = Router()

@router.message(Command('start'))
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    user = get_user_by_telegram(telegram_id)
    if not user:
        register_user(telegram_id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Это бот для питомцев.\n"
        "Команды:\n"
        "/addpet - добавить питомца\n"
        "/post - создать пост\n"
        "/feed - лента\n"
        "/profile - мой профиль\n"
        "/follow @username - подписаться\n"
        "/unfollow @username - отписаться\n"
        "/help - помощь"
    )