# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states import AdminModerationStates
from db import get_all_posts_for_moderation, delete_post, ban_user, unban_user, get_user_by_telegram
from keyboards.inline import admin_post_keyboard
import config
from config import ADMIN_ID
from db import delete_post
router = Router()

@router.callback_query(F.data.startswith("delpost_"))
async def delete_post_callback(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет прав", show_alert=True)
        return
    post_id = int(callback.data.split("_")[1])
    delete_post(post_id)
    await callback.message.delete()
    await callback.answer("Пост удалён", show_alert=False)
    
@router.message(Command('admin'))
async def cmd_admin(message: Message):
    if message.from_user.id not in config.ADMIN_ID:
        await message.answer("Нет прав")
        return
    await message.answer("Админ-панель:\n/posts - все посты\n/ban @username - забанить\n/unban @username - разбанить")

@router.message(Command('posts'))
async def list_posts(message: Message):
    if message.from_user.id not in config.ADMIN_ID:
        return
    posts = get_all_posts_for_moderation()
    if not posts:
        await message.answer("Нет постов")
        return
    for post in posts[:5]:  # лимит
        post_id, file_id, file_type, caption, created_at, username, telegram_id = post
        text = f"Пост {post_id} от @{username}\n{caption or ''}\n{created_at}"
        if file_type == 'photo':
            await message.answer_photo(photo=file_id, caption=text, reply_markup=admin_post_keyboard(post_id))
        else:
            await message.answer_video(video=file_id, caption=text, reply_markup=admin_post_keyboard(post_id))

@router.callback_query(F.data.startswith("admin_del_"))
async def delete_post_callback(callback: CallbackQuery):
    if callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("Нет прав")
        return
    post_id = int(callback.data.split("_")[2])
    delete_post(post_id)
    await callback.message.edit_text("Пост удалён")
    await callback.answer()

@router.message(Command('ban'))
async def ban_user_cmd(message: Message):
    if message.from_user.id not in config.ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Использование: /ban @username")
        return
    username = parts[1].lstrip('@')
    # нужно найти telegram_id по username - для простоты пропустим, можно добавить
    await message.answer("Функция бана требует прямой ID.")

@router.message(Command('unban'))
async def unban_user_cmd(message: Message):
    await message.answer("Функция unban требует прямой ID.")