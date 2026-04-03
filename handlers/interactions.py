# handlers/interactions.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from states import CommentStates
from db import like_post, unlike_post, add_comment, get_user_by_telegram
from db import follow
router = Router()

@router.callback_query(F.data.startswith("like_"))
async def like_callback(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram(callback.from_user.id)
    if not user or user[4]:
        await callback.answer("Вы не зарегистрированы или забанены")
        return
    # Проверяем, лайкал ли уже (упрощённо: просто переключаем)
    # Для простоты будем всегда добавлять лайк (без проверки)
    like_post(callback.from_user.id, post_id)
    await callback.answer("Лайк поставлен!", show_alert=False)

@router.callback_query(F.data.startswith("comment_"))
async def comment_callback(callback: CallbackQuery, state: FSMContext):
    post_id = int(callback.data.split("_")[1])
    await state.update_data(comment_post_id=post_id)
    await state.set_state(CommentStates.waiting_for_text)
    await callback.message.answer("Напишите ваш комментарий:")
    await callback.answer()

@router.message(CommentStates.waiting_for_text)
async def process_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    post_id = data['comment_post_id']
    user = get_user_by_telegram(message.from_user.id)
    if user and not user[4]:
        add_comment(message.from_user.id, post_id, message.text)
        await message.answer("Комментарий добавлен!")
    else:
        await message.answer("Ошибка")
    await state.clear()

def post_action_keyboard(post_id, author_telegram_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{post_id}"),
         InlineKeyboardButton(text="💬 Коммент", callback_data=f"comment_{post_id}")],
        [InlineKeyboardButton(text="➕ Подписаться", callback_data=f"follow_{author_telegram_id}")]
    ])

@router.callback_query(F.data.startswith("like_"))
async def like_callback(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[1])
    like_post(callback.from_user.id, post_id)
    new_count = get_likes_count(post_id)
    await callback.answer(f"❤️ {new_count}", show_alert=False)
    from config import ADMIN_ID
    is_admin = (callback.from_user.id == ADMIN_ID)
    new_keyboard = post_buttons(post_id, new_count, is_admin)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)

@router.callback_query(F.data.startswith("like_"))
async def like_callback(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[1])
    like_post(callback.from_user.id, post_id)
    new_count = get_likes_count(post_id)
    await callback.answer(f"❤️ {new_count}", show_alert=False)
    from config import ADMIN_ID
    is_admin = (callback.from_user.id == ADMIN_ID)
    new_keyboard = post_buttons(post_id, new_count, is_admin)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)