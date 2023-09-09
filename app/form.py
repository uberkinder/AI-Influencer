from aiogram.fsm.state import State, StatesGroup


class AvatarForm(StatesGroup):
    gender = State()
    age_group = State()
    race = State()
    special_features = State()
    clothing_style = State()
    emotion = State()
    style = State()
    background = State()
