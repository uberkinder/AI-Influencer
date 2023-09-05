from aiogram.fsm.state import State, StatesGroup


class UserForm(StatesGroup):
    name = State()
    age = State()
    image_prompt = State()
