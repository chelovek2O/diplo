from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from db import get_user_pets, add_pet, delete_pet, is_user_banned
from keyboards.inline import main_menu, cancel_button, my_pets_keyboard, confirm_delete_pet_keyboard, back_to_main_button
from states import AddPetStates

router = Router()


@router.callback_query(F.data == "add_pet")
async def add_pet_start(callback: CallbackQuery, state: FSMContext):
    if is_user_banned(callback.from_user.id):
        await callback.answer("Вы забанены и не можете добавлять питомцев.", show_alert=True)
        return
    await state.set_state(AddPetStates.waiting_for_name)
    await callback.message.edit_text("Введите имя питомца:", reply_markup=cancel_button())
    await callback.answer()


@router.message(AddPetStates.waiting_for_name, F.text)
async def add_pet_name(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("Вы забанены.")
        await state.clear()
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddPetStates.waiting_for_species)
    await message.answer("Теперь введите вид (например: кот, собака, хомяк):", reply_markup=cancel_button())


@router.message(AddPetStates.waiting_for_species, F.text)
async def add_pet_species(message: Message, state: FSMContext):
    if is_user_banned(message.from_user.id):
        await message.answer("Вы забанены.")
        await state.clear()
        return
    species = message.text.strip()
    data = await state.get_data()
    name = data['name']
    add_pet(message.from_user.id, name, species, file_id=None)
    await state.clear()
    await message.answer(f"✅ Питомец {name} ({species}) добавлен!", reply_markup=main_menu())


@router.callback_query(F.data == "my_pets")
async def show_my_pets(callback: CallbackQuery):
    pets = get_user_pets(callback.from_user.id)
    if not pets:
        await callback.message.answer("У вас ещё нет питомцев. Добавьте через 'Добавить питомца'.",
                                      reply_markup=back_to_main_button())
        await callback.message.delete()
        await callback.answer()
        return
    text = "🐾 Ваши питомцы:\n"
    for pet in pets:
        text += f"- {pet[1]} ({pet[2]})\n"
    keyboard = my_pets_keyboard(pets)
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("del_pet_"))
async def delete_pet_confirm(callback: CallbackQuery):
    pet_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("Вы уверены, что хотите удалить этого питомца? Все его посты также будут удалены.",
                                     reply_markup=confirm_delete_pet_keyboard(pet_id))
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_pet_"))
async def delete_pet_execute(callback: CallbackQuery):
    pet_id = int(callback.data.split("_")[3])
    delete_pet(pet_id, callback.from_user.id)
    await callback.message.answer("Питомец и все его посты удалены.", reply_markup=main_menu())
    await callback.message.delete()
    await callback.answer()