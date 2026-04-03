# handlers/posts.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states import CreatePostStates
from db import get_user_pets, create_post, get_feed, get_likes_count, get_comments, get_user_by_telegram
from keyboards.inline import pet_choice_keyboard, post_action_keyboard
from aiogram import Bot
import config
from db import follow
router = Router()

@router.message(Command('post'))
async def cmd_post(message: Message, state: FSMContext):
    pets = get_user_pets(message.from_user.id)
    if not pets:
        await message.answer("У вас нет питомцев. Добавьте через /addpet")
        return
    await state.set_state(CreatePostStates.waiting_for_pet)
    await message.answer("Выберите питомца:", reply_markup=pet_choice_keyboard(pets))

@router.callback_query(CreatePostStates.waiting_for_pet, F.data.startswith("post_pet_"))
async def select_pet(callback: CallbackQuery, state: FSMContext):
    pet_id = int(callback.data.split("_")[2])
    await state.update_data(pet_id=pet_id)
    await state.set_state(CreatePostStates.waiting_for_media)
    await callback.message.answer("Отправьте фото или видео с подписью (можно без подписи)")
    await callback.answer()

@router.message(CreatePostStates.waiting_for_media, F.photo | F.video)
async def process_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pet_id = data['pet_id']
    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    file_type = "photo" if message.photo else "video"
    caption = message.caption or ""
    user = get_user_by_telegram(message.from_user.id)
    if user and not user[4]:
        post_id = create_post(message.from_user.id, pet_id, file_id, file_type, caption)
        if post_id:
            await message.answer("Пост опубликован!")
        else:
            await message.answer("Ошибка")
    else:
        await message.answer("Вы забанены.")
    await state.clear()

@router.message(CreatePostStates.waiting_for_media)
async def wrong_media(message: Message):
    await message.answer("Пожалуйста, отправьте фото или видео.")

@router.message(Command('feed'))
async def cmd_feed(message: Message, bot: Bot):
    feed = get_feed(message.from_user.id)
    if not feed:
        await message.answer("Лента пуста. Подпишитесь на кого-нибудь или создайте пост.")
        return
    for post in feed:
        post_id, file_id, file_type, caption, created_at, username, pet_name, author_id = post
        likes = get_likes_count(post_id)
        comments = get_comments(post_id)
        text = f"@{username} | {pet_name}\n{caption or ''}\n❤️ {likes}  💬 {len(comments)}"
        if file_type == 'photo':
            await bot.send_photo(chat_id=message.chat.id, photo=file_id, caption=text)
        else:
            await bot.send_video(chat_id=message.chat.id, video=file_id, caption=text)
        # клавиатура действий
        is_admin = (message.from_user.id == ADMIN_ID)
        keyboard = post_buttons(post_id, likes, is_admin)

        await bot.send_message(chat_id=message.chat.id, text="Действия:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("follow_"))
async def follow_callback(callback: CallbackQuery):
    author_telegram = int(callback.data.split("_")[1])
    follow(callback.from_user.id, author_telegram)
    await callback.answer("Подписались!", show_alert=False)



# ---------- ПРОФИЛЬ (ПОКАЗЫВАЕТ ПИТОМЦЕВ И ПОСТЫ) ----------
@router.message(Command('profile'))
async def profile_cmd(message: Message):
    from db import get_user_pets, get_user_posts, get_likes_count, get_comments
    pets = get_user_pets(message.from_user.id)
    text = "🐾 Ваши питомцы:\n"
    if pets:
        for p in pets:
            text += f"- {p[1]} ({p[2]})\n"
    else:
        text += "Нет питомцев. Добавьте через /addpet\n"
    
    posts = get_user_posts(message.from_user.id)
    text += f"\n📸 Ваши посты: {len(posts)}\n"
    await message.answer(text)
    
    for post in posts[:5]:
        post_id = post[0]
        file_id = post[1]
        file_type = post[2]
        caption = post[3] or ""
        pet_name = post[5] or "без питомца"
        likes = get_likes_count(post_id)
        comments = get_comments(post_id)
        info = f"🐕 {pet_name}\n{caption}\n❤️ {likes}  💬 {len(comments)}"
        if file_type == "photo":
            await message.answer_photo(photo=file_id, caption=info)
        else:
            await message.answer_video(video=file_id, caption=info)



