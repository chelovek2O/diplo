from aiogram.fsm.state import State, StatesGroup

class AddPetStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_species = State()

class PostStates(StatesGroup):
    waiting_for_pet = State()
    waiting_for_media = State()

class AdminStates(StatesGroup):
    waiting_for_target_username = State()