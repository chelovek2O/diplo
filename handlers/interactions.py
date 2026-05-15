from aiogram import Router, F
from aiogram.types import CallbackQuery
from db import like_post, get_likes_count, is_user_banned

router = Router()


@router.callback_query(F.data.startswith("like_"))
async def like_callback(callback: CallbackQuery):
    if is_user_banned(callback.from_user.id):
        await callback.answer("Вы забанены и не можете ставить лайки.", show_alert=True)
        return
    
    post_id = int(callback.data.split("_")[1])
    like_post(callback.from_user.id, post_id)
    new_count = get_likes_count(post_id)
    await callback.answer(f"❤️ {new_count}", show_alert=False)