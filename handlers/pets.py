# handlers/pets.py
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from states import AddPetStates
from db import add_pet, get_user_by_telegram
import config

router = Router()

@router.message(Command('addpet'))
async def cmd_addpet(message: Message, state: FSMContext):
    await state.set_state(AddPetStates.waiting_for_name)
    await message.answer("Введите имя питомца:")

@router.message(AddPetStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddPetStates.waiting_for_species)
    await message.answer("Введите вид (кот, собака и т.п.):")

@router.message(AddPetStates.waiting_for_species)
async def process_species(message: Message, state: FSMContext):
    await state.update_data(species=message.text)
    await state.set_state(AddPetStates.waiting_for_photo)
    await message.answer("Теперь отправьте ФОТО питомца:")

@router.message(AddPetStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    species = data['species']
    file_id = message.photo[-1].file_id
    user = get_user_by_telegram(message.from_user.id)
    if user and not user[4]:  # не забанен
        add_pet(message.from_user.id, name, species, file_id)
        await message.answer(f"Питомец {name} ({species}) добавлен!")
    else:
        await message.answer("Вы забанены или не зарегистрированы.")
    await state.clear()

@router.message(AddPetStates.waiting_for_photo)
async def wrong_photo(message: Message):
    await message.answer("Пожалуйста, отправьте фото.")