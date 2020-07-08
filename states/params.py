from aiogram.dispatcher.filters.state import StatesGroup, State


class UserParams(StatesGroup):
    SetTime = State()
    SetCity = State()
    SetNewsTopic = State()


class GroupParams(StatesGroup):
    SetHours = State()
    SetNewsTopics = State()
