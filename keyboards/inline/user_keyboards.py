from aiogram import types


quantity_news_markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="1", callback_data='private_chat_news_1'),
                types.InlineKeyboardButton(text="2", callback_data='private_chat_news_2'),
                types.InlineKeyboardButton(text="3", callback_data='private_chat_news_3'),
            ],
            [
                types.InlineKeyboardButton(text="4", callback_data='private_chat_news_4'),
                types.InlineKeyboardButton(text="5", callback_data='private_chat_news_5'),
            ],
            [
                types.InlineKeyboardButton(text="Отмена", callback_data='private_chat_news_cancel'),
            ]
        ]
    )

donate_markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="QIWI", url='qiwi.com/n/ANDRUS', callback_data='private_chat_donate_QIWI')],
            [types.InlineKeyboardButton(text="Номер карты (Сбербанк)", callback_data='private_chat_donate_Sberbank')],
            [types.InlineKeyboardButton(text="Отмена", callback_data='private_chat_donate_cancel')]
        ]
    )

