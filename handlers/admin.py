# handlers/admin.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from db import get_user, ban_user, unban_user, get_posts_by_user, delete_post, is_user_banned
from keyboards.inline import admin_user_actions_keyboard, admin_posts_keyboard, main_menu, back_to_main_button
from states import AdminStates
from config import ADMIN_ID

router = Router()

@router.message(Command('admin'))
async def admin_cmd(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к админ-панели.")
        return
    await message.answer(
        "🛡 Админ-панель\nВведите Telegram username (без @) или ID пользователя, которым хотите управлять:",
        reply_markup=back_to_main_button()
    )
    await state.set_state(AdminStates.waiting_for_target_username)

@router.message(AdminStates.waiting_for_target_username)
async def admin_get_target_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    input_text = message.text.strip()
    target_telegram_id = None
    if input_text.isdigit():
        target_telegram_id = int(input_text)
    else:
        username = input_text.lstrip('@')
        import sqlite3
        conn = sqlite3.connect('pets.db')
        cur = conn.cursor()
        cur.execute('SELECT telegram_id FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if row:
            target_telegram_id = row[0]
    if not target_telegram_id:
        await message.answer("Пользователь не найден. Попробуйте ещё раз.")
        return
    await state.update_data(target_telegram_id=target_telegram_id)
    await show_admin_user_actions(message, target_telegram_id, state)

async def show_admin_user_actions(message: Message, target_telegram_id: int, state: FSMContext):
    user = get_user(target_telegram_id)
    if not user:
        await message.answer("Пользователь не найден.")
        await state.clear()
        return
    is_banned = is_user_banned(target_telegram_id)
    text = f"👤 Пользователь: @{user[2]} (ID: {target_telegram_id})\nСтатус: {'🔴 Забанен' if is_banned else '🟢 Активен'}"
    keyboard = admin_user_actions_keyboard(target_telegram_id, is_banned)
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_panel_back")
async def admin_panel_back(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите username или ID пользователя:", reply_markup=back_to_main_button())
    await state.set_state(AdminStates.waiting_for_target_username)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_") & F.data[11:].isdigit())
async def admin_user_actions(callback: CallbackQuery, state: FSMContext):
    target_telegram_id = int(callback.data.split("_")[2])
    await state.update_data(target_telegram_id=target_telegram_id)
    user = get_user(target_telegram_id)
    if not user:
        await callback.message.edit_text("Пользователь не найден.", reply_markup=main_menu())
        await callback.answer()
        return
    is_banned = is_user_banned(target_telegram_id)
    text = f"👤 Пользователь: @{user[2]} (ID: {target_telegram_id})\nСтатус: {'🔴 Забанен' if is_banned else '🟢 Активен'}"
    keyboard = admin_user_actions_keyboard(target_telegram_id, is_banned)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_user_posts_"))
async def admin_show_user_posts(callback: CallbackQuery):
    target_telegram_id = int(callback.data.split("_")[3])
    posts = get_posts_by_user(target_telegram_id)
    if not posts:
        await callback.message.edit_text("У пользователя нет постов.",
                                         reply_markup=admin_user_actions_keyboard(target_telegram_id, is_user_banned(target_telegram_id)))
        await callback.answer()
        return
    keyboard = admin_posts_keyboard(posts, target_telegram_id)
    await callback.message.edit_text(f"Посты пользователя (всего {len(posts)}):", reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("admin_delpost_"))
async def admin_delete_post(callback: CallbackQuery):
    parts = callback.data.split("_")
    post_id = int(parts[2])
    target_telegram_id = int(parts[3])
    delete_post(post_id, is_admin=True)
    posts = get_posts_by_user(target_telegram_id)
    if posts:
        keyboard = admin_posts_keyboard(posts, target_telegram_id)
        await callback.message.edit_text(f"Посты пользователя (обновлено, {len(posts)}):", reply_markup=keyboard)
    else:
        await callback.message.edit_text("Посты удалены. У пользователя больше нет постов.",
                                         reply_markup=admin_user_actions_keyboard(target_telegram_id, is_user_banned(target_telegram_id)))
    await callback.answer("Пост удалён", show_alert=False)

@router.callback_query(F.data.startswith("admin_ban_"))
async def admin_ban_user(callback: CallbackQuery):
    target_telegram_id = int(callback.data.split("_")[2])
    ban_user(target_telegram_id, hours=24)
    await callback.answer("Пользователь забанен на 24 часа", show_alert=False)
    user = get_user(target_telegram_id)
    text = f"👤 Пользователь: @{user[2]} (ID: {target_telegram_id})\nСтатус: 🔴 Забанен"
    keyboard = admin_user_actions_keyboard(target_telegram_id, is_banned=True)
    await callback.message.edit_text(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("admin_unban_"))
async def admin_unban_user(callback: CallbackQuery):
    target_telegram_id = int(callback.data.split("_")[2])
    unban_user(target_telegram_id)
    await callback.answer("Пользователь разбанен", show_alert=False)
    user = get_user(target_telegram_id)
    text = f"👤 Пользователь: @{user[2]} (ID: {target_telegram_id})\nСтатус: 🟢 Активен"
    keyboard = admin_user_actions_keyboard(target_telegram_id, is_banned=False)
    await callback.message.edit_text(text, reply_markup=keyboard)