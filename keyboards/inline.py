# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def pet_choice_keyboard(pets):
    buttons = []
    for pet_id, name, species in pets:
        buttons.append([InlineKeyboardButton(text=f"{name} ({species})", callback_data=f"post_pet_{pet_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def post_action_keyboard(post_id, user_liked=False):
    like_text = "❤️ Лайк" if not user_liked else "❤️ Убрать лайк"
    buttons = [
        [InlineKeyboardButton(text=like_text, callback_data=f"like_{post_id}"),
         InlineKeyboardButton(text="💬 Коммент", callback_data=f"comment_{post_id}")],
        [InlineKeyboardButton(text="👤 Подписаться", callback_data=f"follow_author")]  # упростим
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_post_keyboard(post_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Удалить пост", callback_data=f"admin_del_{post_id}")]
    ])

def post_buttons(post_id, likes_count, is_admin=False):
    buttons = [
        InlineKeyboardButton(text=f"❤️ {likes_count}", callback_data=f"like_{post_id}"),
        InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{post_id}")
    ]
    if is_admin:
        buttons.append(InlineKeyboardButton(text="❌ Удалить", callback_data=f"delpost_{post_id}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])