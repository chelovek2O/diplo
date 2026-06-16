from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🐾 Добавить питомца", callback_data="add_pet")],
        [InlineKeyboardButton(text="📋 Мои питомцы", callback_data="my_pets")],
        [InlineKeyboardButton(text="📝 Создать пост", callback_data="create_post")],
        [InlineKeyboardButton(text="📰 Лента подписок", callback_data="feed")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔔 Мои подписки", callback_data="my_subscriptions")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])

def back_to_main_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])

def pets_keyboard(pets):
    buttons = []
    for pet in pets:
        pet_id, name, species, _ = pet
        buttons.append([InlineKeyboardButton(text=f"{name} ({species})", callback_data=f"pet_{pet_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def my_pets_keyboard(pets):
    buttons = []
    for pet in pets:
        pet_id, name, species, _ = pet
        buttons.append([InlineKeyboardButton(text=f"{name} ({species})", callback_data=f"select_pet_{pet_id}"),
                        InlineKeyboardButton(text="❌ Удалить", callback_data=f"del_pet_{pet_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_delete_pet_keyboard(pet_id):
    buttons = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm_del_pet_{pet_id}"),
         InlineKeyboardButton(text="❌ Нет", callback_data="my_pets")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def feed_navigation_buttons(post_index, total_posts, is_subscribed, author_telegram_id, current_user_id, post_id):
    nav_buttons = []
    if post_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Предыдущий", callback_data="feed_prev"))
    if post_index < total_posts - 1:
        nav_buttons.append(InlineKeyboardButton(text="Следующий ▶️", callback_data="feed_next"))
    nav_buttons.append(InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{post_id}"))
    if author_telegram_id != current_user_id:
        if is_subscribed:
            nav_buttons.append(InlineKeyboardButton(text="🔔 Отписаться", callback_data=f"feed_unsub_{author_telegram_id}"))
        else:
            nav_buttons.append(InlineKeyboardButton(text="➕ Подписаться", callback_data=f"feed_sub_{author_telegram_id}"))
    nav_buttons.append(InlineKeyboardButton(text="🔙 Меню", callback_data="back_to_main"))
    keyboard = []
    for i in range(0, len(nav_buttons), 2):
        if i + 1 < len(nav_buttons):
            keyboard.append([nav_buttons[i], nav_buttons[i+1]])
        else:
            keyboard.append([nav_buttons[i]])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def subscriptions_keyboard(subscriptions_list):
    buttons = []
    for sub in subscriptions_list:
        sub_telegram_id, username, first_name = sub
        display = f"@{username}" if username else first_name
        buttons.append([InlineKeyboardButton(text=f"{display}", callback_data="ignore"),
                        InlineKeyboardButton(text="❌ Отписаться", callback_data=f"unsub_{sub_telegram_id}")])
    buttons.append([InlineKeyboardButton(text="➕ Подписаться", callback_data="subscribe_new")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_user_actions_keyboard(target_telegram_id, is_banned):
    buttons = []
    buttons.append([InlineKeyboardButton(text="📸 Посты пользователя", callback_data=f"admin_user_posts_{target_telegram_id}")])
    if is_banned:
        buttons.append([InlineKeyboardButton(text="🔓 Разбан", callback_data=f"admin_unban_{target_telegram_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔨 Забанить (24ч)", callback_data=f"admin_ban_{target_telegram_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_posts_keyboard(posts, target_telegram_id):
    buttons = []
    for post in posts:
        post_id = post[0]
        pet_name = post[5] or "без питомца"
        caption_preview = (post[3][:30] + '...') if post[3] else ''
        text = f"ID:{post_id} {pet_name} | {caption_preview}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"admin_delpost_{post_id}_{target_telegram_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад к пользователю", callback_data=f"admin_user_{target_telegram_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)