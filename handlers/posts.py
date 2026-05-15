from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from db import (
    get_user_pets, create_post, get_post_by_index, get_likes_count, 
    delete_post, is_user_banned, is_subscribed, add_subscription, 
    remove_subscription, get_posts_by_pet
)
from keyboards.inline import (
    pets_keyboard, main_menu, cancel_button, back_to_main_button, 
    feed_navigation_buttons, my_pets_keyboard
)
from states import PostStates
from config import ADMIN_ID, TOKEN
 
bot = Bot(token=TOKEN)
router = Router()
user_feed_index = {}


# ---------- СОЗДАНИЕ ПОСТА ----------
@router.callback_query(F.data == "create_post")
async def create_post_start(callback: CallbackQuery, state: FSMContext):
    if is_user_banned(callback.from_user.id):
        await callback.answer("Вы забанены и не можете создавать посты.", show_alert=True)
        return
    pets = get_user_pets(callback.from_user.id)
    if not pets:
        await callback.message.edit_text("Сначала добавьте питомца через 'Добавить питомца'.",
                                         reply_markup=back_to_main_button())
        await callback.answer()
        return
    await state.set_state(PostStates.waiting_for_pet)
    await callback.message.edit_text("Выберите питомца для публикации:", reply_markup=pets_keyboard(pets))
    await callback.answer()


@router.callback_query(PostStates.waiting_for_pet, F.data.startswith("pet_"))
async def select_pet_for_post(callback: CallbackQuery, state: FSMContext):
    pet_id = int(callback.data.split("_")[1])
    await state.update_data(pet_id=pet_id)
    await state.set_state(PostStates.waiting_for_media)
    await callback.message.edit_text("Теперь отправьте ФОТО или ВИДЕО с подписью (описанием).", reply_markup=cancel_button())
    await callback.answer()


@router.message(PostStates.waiting_for_media, F.photo | F.video)
async def publish_post(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("Вы забанены.")
        await state.clear()
        return
    data = await state.get_data()
    pet_id = data.get('pet_id')
    if not pet_id:
        await message.answer("Ошибка, начните заново.", reply_markup=main_menu())
        await state.clear()
        return
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    file_type = "photo" if message.photo else "video"
    caption = message.caption or ""
    create_post(message.from_user.id, pet_id, file_id, file_type, caption)
    await message.answer("✅ Пост опубликован!", reply_markup=main_menu())
    await state.clear()


# ---------- ЛЕНТА ПОДПИСОК ----------
@router.callback_query(F.data == "feed")
async def feed_start(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_feed_index[user_id] = 0
    await send_feed_post(callback.message.chat.id, user_id, callback)


async def send_feed_post(chat_id, user_id, callback=None):
    index = user_feed_index.get(user_id, 0)
    post_data, total = get_post_by_index(user_id, index)
    
    if not post_data:
        if callback:
            await callback.message.delete()
            await callback.message.answer("Лента пуста. Подпишитесь на других пользователей или создайте пост.",
                                          reply_markup=back_to_main_button())
            if callback:
                await callback.answer()
        return
    
    post_id = post_data[0]
    file_id = post_data[1]
    file_type = post_data[2]
    caption = post_data[3] or ""
    author_username = post_data[5]
    author_telegram_id = post_data[6]
    pet_name = post_data[7] or "без питомца"
    likes = get_likes_count(post_id)
    subscribed = is_subscribed(user_id, author_telegram_id) if author_telegram_id != user_id else True
    
    text = f"📸 Пост {index+1} из {total}\n@{author_username} | {pet_name}\n{caption}\n❤️ {likes}"
    keyboard = feed_navigation_buttons(index, total, subscribed, author_telegram_id, user_id, post_id)
    
    # Отправляем новое сообщение
    if file_type == "photo":
        await bot.send_photo(chat_id=chat_id, photo=file_id, caption=text, reply_markup=keyboard)
    else:
        await bot.send_video(chat_id=chat_id, video=file_id, caption=text, reply_markup=keyboard)
    
    # Удаляем предыдущее сообщение, если оно было от меню
    if callback:
        await callback.message.delete()
        await callback.answer()


@router.callback_query(F.data == "feed_prev")
async def feed_prev(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = user_feed_index.get(user_id, 0)
    if current > 0:
        user_feed_index[user_id] = current - 1
        await callback.message.delete()
        await send_feed_post(callback.message.chat.id, user_id, None)
    await callback.answer()


@router.callback_query(F.data == "feed_next")
async def feed_next(callback: CallbackQuery):
    user_id = callback.from_user.id
    current = user_feed_index.get(user_id, 0)
    _, total = get_post_by_index(user_id, 0)
    if total and current < total - 1:
        user_feed_index[user_id] = current + 1
        await callback.message.delete()
        await send_feed_post(callback.message.chat.id, user_id, None)
    await callback.answer()


@router.callback_query(F.data.startswith("feed_sub_"))
async def feed_subscribe(callback: CallbackQuery):
    author_telegram_id = int(callback.data.split("_")[2])
    if add_subscription(callback.from_user.id, author_telegram_id):
        await callback.answer("Вы подписались на автора!", show_alert=False)
    else:
        await callback.answer("Не удалось подписаться", show_alert=False)
    user_id = callback.from_user.id
    await callback.message.delete()
    await send_feed_post(callback.message.chat.id, user_id, None)


@router.callback_query(F.data.startswith("feed_unsub_"))
async def feed_unsubscribe(callback: CallbackQuery):
    author_telegram_id = int(callback.data.split("_")[2])
    remove_subscription(callback.from_user.id, author_telegram_id)
    await callback.answer("Вы отписались от автора", show_alert=False)
    user_id = callback.from_user.id
    await callback.message.delete()
    await send_feed_post(callback.message.chat.id, user_id, None)


# ---------- ПРОФИЛЬ (ВЫБОР ПИТОМЦА → ПОСТЫ ПИТОМЦА) ----------
@router.callback_query(F.data == "profile")
async def profile_show_pets(callback: CallbackQuery):
    pets = get_user_pets(callback.from_user.id)
    if not pets:
        await callback.message.edit_text("У вас ещё нет питомцев. Добавьте через 'Добавить питомца'.",
                                         reply_markup=back_to_main_button())
        await callback.answer()
        return
    text = "🐾 Выберите питомца, чтобы посмотреть его посты:"
    keyboard = my_pets_keyboard(pets)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("select_pet_"))
async def profile_show_pet_posts(callback: CallbackQuery):
    pet_id = int(callback.data.split("_")[2])
    posts = get_posts_by_pet(callback.from_user.id, pet_id)
    pets = get_user_pets(callback.from_user.id)
    pet_name = next((p[1] for p in pets if p[0] == pet_id), "питомца")
    
    if not posts:
        await callback.message.edit_text(f"У питомца {pet_name} пока нет постов.",
                                         reply_markup=back_to_main_button())
        await callback.answer()
        return
    
    await callback.message.edit_text(f"📸 Посты питомца {pet_name} (всего {len(posts)}):", 
                                     reply_markup=back_to_main_button())
    
    for post in posts:
        post_id = post[0]
        file_id = post[1]
        file_type = post[2]
        caption = post[3] or ""
        likes = get_likes_count(post_id)
        info = f"📝 {caption}\n❤️ {likes} лайков"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Удалить пост", callback_data=f"del_own_post_{post_id}")]
        ])
        if file_type == "photo":
            await callback.message.answer_photo(photo=file_id, caption=info, reply_markup=keyboard)
        else:
            await callback.message.answer_video(video=file_id, caption=info, reply_markup=keyboard)
    
    await callback.answer()


# ---------- УДАЛЕНИЕ СВОЕГО ПОСТА (ТОЛЬКО В ПРОФИЛЕ) ----------
@router.callback_query(F.data.startswith("del_own_post_"))
async def delete_own_post(callback: CallbackQuery):
    post_id = int(callback.data.split("_")[3])
    delete_post(post_id, user_telegram_id=callback.from_user.id, is_admin=False)
    await callback.message.delete()
    await callback.answer("Пост удалён", show_alert=False)
    # Возвращаем в меню выбора питомцев
    pets = get_user_pets(callback.from_user.id)
    if pets:
        await callback.message.answer("Выберите питомца:", reply_markup=my_pets_keyboard(pets))
    else:
        await callback.message.answer("Главное меню:", reply_markup=main_menu())