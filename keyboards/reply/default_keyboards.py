from aiogram import types

default_user_markup = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text='🌤Погода'),
            types.KeyboardButton(text='👔Курсы валют')
        ],
        [
            types.KeyboardButton(text='🧐Новости')
        ],
    ],
    resize_keyboard=True
)

default_group_markup = types.ReplyKeyboardMarkup(
    keyboard=[
        [
            types.KeyboardButton(text='🧐Новости'),
            types.KeyboardButton(text='👔Курсы валют')
        ],
    ],
    resize_keyboard=True
)