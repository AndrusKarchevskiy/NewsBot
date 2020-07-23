from aiogram import types

quantity_news_markup = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="1", callback_data='group_news_1'),
            types.InlineKeyboardButton(text="2", callback_data='group_news_2'),
            types.InlineKeyboardButton(text="3", callback_data='group_news_3'),
        ],
        [
            types.InlineKeyboardButton(text="Отмена", callback_data='group_news_cancel'),
        ]
    ]
)
