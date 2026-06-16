from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from db import get_user_subscriptions, add_subscription, remove_subscription, get_user_by_username
from keyboards.inline import subscriptions_keyboard, main_menu, back_to_main_button

router = Router()
temp_subscribe = {}


@router.callback_query(F.data == "my_subscriptions")
async def show_subscriptions(callback: CallbackQuery):
    subs = get_user_subscriptions(callback.from_user.id)
    if not subs:
        await callback.message.answer("Вы ни на кого не подписаны.\nИспользуйте '➕ Подписаться', чтобы добавить автора.",
                                      reply_markup=subscriptions_keyboard([]))
        await callback.message.delete()
    else:
        text = "🔔 Ваши подписки:\n"
        for sub in subs:
            _, username, first_name = sub
            display = f"@{username}" if username else first_name
            text += f"- {display}\n"
        await callback.message.answer(text, reply_markup=subscriptions_keyboard(subs))
        await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data == "subscribe_new")
async def subscribe_new(callback: CallbackQuery):
    await callback.message.edit_text("Введите Telegram ID или @username пользователя, на которого хотите подписаться:",
                                     reply_markup=back_to_main_button())
    temp_subscribe[callback.from_user.id] = True
    await callback.answer()


@router.message(F.text)
async def handle_subscribe_input(message: Message, state: FSMContext):
    if message.from_user.id not in temp_subscribe:
        return
    del temp_subscribe[message.from_user.id]
    input_text = message.text.strip()
    target_id = None
    if input_text.isdigit():
        target_id = int(input_text)
    else:
        username = input_text.lstrip('@')
        user_data = get_user_by_username(username)
        if user_data:
            target_id = user_data[0]
    if not target_id:
        await message.answer("Пользователь не найден. Попробуйте снова.", reply_markup=main_menu())
        return
    if target_id == message.from_user.id:
        await message.answer("Нельзя подписаться на себя.", reply_markup=main_menu())
        return
    if add_subscription(message.from_user.id, target_id):
        await message.answer("✅ Вы подписались на пользователя!", reply_markup=main_menu())
    else:
        await message.answer("Не удалось подписаться (возможно уже подписаны).", reply_markup=main_menu())


@router.callback_query(F.data.startswith("unsub_"))
async def unsubscribe(callback: CallbackQuery):
    author_id = int(callback.data.split("_")[1])
    remove_subscription(callback.from_user.id, author_id)
    await callback.answer("Вы отписались", show_alert=False)
    subs = get_user_subscriptions(callback.from_user.id)
    if not subs:
        await callback.message.answer("Вы ни на кого не подписаны.", reply_markup=subscriptions_keyboard([]))
        await callback.message.delete()
    else:
        text = "🔔 Ваши подписки:\n"
        for sub in subs:
            _, username, first_name = sub
            display = f"@{username}" if username else first_name
            text += f"- {display}\n"
        await callback.message.answer(text, reply_markup=subscriptions_keyboard(subs))
        await callback.message.delete()