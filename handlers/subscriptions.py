# handlers/subscriptions.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db import follow, unfollow
import re

router = Router()

@router.message(Command('follow'))
async def cmd_follow(message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /follow @username")
        return
    username = parts[1].lstrip('@')
    # здесь нужно получить telegram_id по username - в простом варианте не реализовано
    # для демо просто скажем, что не реализовано
    await message.answer("Функция подписки по username требует дополнительной логики. Пока доступна только через админку.")
    # В реальности нужно хранить username -> telegram_id, но для простоты можно попросить пользователя ввести ID.
    # Оставим заглушку.

@router.message(Command('unfollow'))
async def cmd_unfollow(message: Message):
    await message.answer("Аналогично /follow")