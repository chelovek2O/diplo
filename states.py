# states.py
from aiogram.fsm.state import State, StatesGroup

class AddPetStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_species = State()
    waiting_for_photo = State()

class CreatePostStates(StatesGroup):
    waiting_for_pet = State()
    waiting_for_media = State()

class CommentStates(StatesGroup):
    waiting_for_text = State()

class AdminModerationStates(StatesGroup):
    waiting_for_post_id = State()