from aiogram.dispatcher.filters.state import StatesGroup, State


class Params(StatesGroup):
    SetTime = State()
    SetCity = State()
    SetNewsTopic = State()
