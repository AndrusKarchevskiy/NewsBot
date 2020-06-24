import logging

from aiogram import Bot, Dispatcher, executor, types

from pyowm import OWM  # API для работы с погодой
from newsapi import NewsApiClient  # API для работы с новостями

import time

from data import db  # Модуль для работы с базой данных

from settings import keys  # Модуль, в котором хранятся Токены от API, "security" информация
from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения
from settings.api import get_news, get_weather  # Модуль, который работает с API погоды, новостей
# Модуль, в котором генерируется ответ на запрос по смене параметра, параметр, если валиден, заносится в БД
from settings.changer_params import change_time, change_city, change_news_topic, change_status
from settings.getter_info import get_all_user_info

logging.basicConfig(level=logging.INFO)

owm = OWM(keys.OWM_TOKEN, language='ru')
news_api = NewsApiClient(api_key=keys.NEWS_TOKEN)

bot = Bot(token=keys.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Выводит приветственное соощение пользователю, активирует 'reply' клавиатуру"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.reply('<b>🤝Здравствуйте, {0.first_name}🤝!</b>'.format(message.from_user))

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item1 = types.KeyboardButton('🌤Погода')
    item2 = types.KeyboardButton('🧐Новости')

    markup.add(item1, item2)
    await message.answer(template_messages.welcome_message, reply_markup=markup)


@dp.message_handler(commands=['help'])
async def show_information(message: types.Message):
    """Отправляет информацию о боте пользователю"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer(template_messages.information_message)


@dp.message_handler(regexp='🌤Погода')
async def send_weather(message: types.Message):
    """Отправляет погоду по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'b_weather'
    db.change_user_parameter(user_id, section, parameter)

    section = 'city'
    city = db.get_user_parameter(user_id, section)
    try:
        weather = get_weather(city)
        await message.answer(weather)

    except Exception as error:
        print(error)
        await message.answer('🤔К сожалению, <b>произошла ошибка</b> во время подключения к серверу. Пожалуйста, '
                             'повторите попытку')


@dp.message_handler(regexp='🧐Новости')
async def send_news(message: types.Message):
    """Отправляет новости по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'b_news'
    db.change_user_parameter(user_id, section, parameter)

    section = 'news_topic'
    news_topic = db.get_user_parameter(user_id, section)

    section = 'quantity_news'
    quantity_news = db.get_user_parameter(user_id, section)

    news_number = 0

    while news_number < quantity_news:
        news = get_news(news_topic, quantity_news, news_number)
        await message.answer(news)

        # Если команда "/set_news_topic" в news - значит, было отправлено сообщение о том, что больше новостей не
        # найдено -> выход из цикла
        if '/set_news_topic' in news:
            break
        time.sleep(1)
        news_number += 1


@dp.message_handler(commands='set_time')
async def set_time(message: types.Message):
    """Изменяет время регулярной отправки погоды и новостей"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_time'
    db.change_user_parameter(user_id, section, parameter)

    if message.text == '/set_time':
        await message.answer('Введите время (по МСК), в которое вы каждый день будете получать '
                             'новости и сводку погоды. Формат: <b>ЧЧ:ММ</b>. Примеры: '
                             '<b>08:20</b>, <b>22:05</b>')

    else:
        new_time = message.text
        message_to_user = change_time(user_id, new_time)
        await message.answer(message_to_user)


@dp.message_handler(commands='set_city')
async def set_city(message: types.Message):
    """Изменяет город, из которого пользователь будет получать сводку погоды"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_city'
    db.change_user_parameter(user_id, section, parameter)

    if message.text == '/set_city':
        await message.answer('Введите город, из которого хотите получать сводку погоды.\nПримеры: '
                             '<b>Санкт-Петербург</b>, <b>Киев</b>, <b>Брянск</b>')

    else:
        new_city = message.text
        message_to_user = change_city(user_id, new_city)
        await message.answer(message_to_user)


@dp.message_handler(commands='set_news_topic')
async def set_news_topic(message: types.Message):
    """Изменяет ключевое слово, по которому отбираются новости"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_news_topic'
    db.change_user_parameter(user_id, section, parameter)

    if message.text == '/set_news_topic':
        await message.answer('Введите ключевое слово (фразу), по которому(ой) вы будете получать новости.\n'
                             'Примеры: <b>Apple</b>, <b>Бизнес</b>, <b>Илон Маск</b>\n\n'
                             '<b>P.S.</b> <i>Если вы хотите получать самые актуальные зарубежные новости, введите '
                             'ключевое слово (фразу) на иностранном языке</i>')

    else:
        new_news_topic = message.text
        message_to_user = change_news_topic(user_id, new_news_topic)
        await message.answer(message_to_user)


@dp.message_handler(commands='reset')
async def reset_settings(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'reset'
    db.change_user_parameter(user_id, section, parameter)

    db.delete_user_info(user_id)
    await message.answer('✔<i>Старые настройки успешно удалены!</i>\n'
                         '✔<i>Новые настройки успешно установлены!</i>\n\n'
                         '<b>Теперь, вы будете ежедневно получать одну новость по ключевому слову "Россия" '
                         'и погоду из Москвы в 08:00 по МСК</b>')

    db.add_new_user(user_id, user_name)


@dp.message_handler(commands='set_status')
async def set_status(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    message_to_user = change_status(user_id)
    await message.answer(message_to_user)


@dp.message_handler(commands='set_quantity_news')
async def set_quantity_news_buttons(message: types.Message):
    """Изменяет количество новостей, которое будет получать пользователь"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)

    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_quantity_news'
    db.change_user_parameter(user_id, section, parameter)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="1", callback_data='news_1'),
                types.InlineKeyboardButton(text="2", callback_data='news_2'),
                types.InlineKeyboardButton(text="3", callback_data='news_3'),
            ],
            [
                types.InlineKeyboardButton(text="4", callback_data='news_4'),
                types.InlineKeyboardButton(text="5", callback_data='news_5'),
            ],
            [
                types.InlineKeyboardButton(text="Отмена", callback_data='news_cancel'),
            ]
        ]
    )

    await message.answer('Выберете количество новостей, которое будете получать. Если вы передумали изменять значение, '
                         'нажмите на кнопку <b>Отмена</b>', reply_markup=markup)


@dp.callback_query_handler(text_contains='news_')
async def change_quantity_news(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = str(call.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await call.answer(cache_time=10)

    callback_data = str(call.data).replace('news_', '')

    if callback_data.isdigit():
        section = 'quantity_news'
        old_quantity_news = db.get_user_parameter(user_id, section)
        message_to_user = f'✔Количество новостей <b>{old_quantity_news}</b> успешно удалено!\n'

        parameter = callback_data
        db.change_user_parameter(user_id, section, parameter)

        message_to_user += f'✔Теперь, вы будете получать новости в количестве <b>{callback_data}</b> за раз!'
        await call.message.answer(message_to_user)

    else:
        await call.message.answer(f'<b>Действие успешно отменено</b>, скрываю клавиатуру😃')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(commands='donate')
async def donate_buttons(message: types.Message):
    """Отправлят кнопки"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'donate'
    db.change_user_parameter(user_id, section, parameter)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="QIWI", url='qiwi.com/n/ANDRUS', callback_data='donate_QIWI')],
            [types.InlineKeyboardButton(text="Номер карты (Сбербанк)", callback_data='donate_Sberbank')],
            [types.InlineKeyboardButton(text="Отмена", callback_data='donate_cancel')]
        ]
    )

    await message.answer('Выберите способ оплаты. Если вы хотите поддержать проект через <b>QIWI</b>, пожалуйста, '
                         'после перевода средств нажмите <b>Отмена</b>, иначе кнопки не пропадут', reply_markup=markup)


@dp.callback_query_handler(text_contains='donate_')
async def donation(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = str(call.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await call.answer(cache_time=10)

    callback_data = str(call.data).replace('donate_', '')

    if callback_data == 'Sberbank':
        await call.message.answer(f'Номер карты (Сбербанк): <b>{keys.CARD_NUMBER} - {keys.MY_NAME}</b>')

    await call.message.answer('<i>Если вы задонатили, большое спасибо! Вы очень мотивируете меня на поддержку '
                              'и улучшение этого бота!🖤\nЕсли вы просто его активный пользователь, '
                              'то знайте, что тоже очень помогаете проекту, продвигаете его среди остальных!</i>😊')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(commands='check_params')
async def check_params(message: types.Message):
    """Отправляет текущие настройки пользователя"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    user_params = get_all_user_info(user_id)
    await message.answer(f'Отправляю ваши текущие настройки:\n\n{user_params}\n\nЕсли вы хотите изменить что-либо, '
                         f'воспользуйтесь остальными командами!😃')


@dp.message_handler()
async def message_control(message: types.Message):
    """Обрабатывает все текстовые сообщения. В функциях, при вводе значений после ввода команды,
    значение отправляется обратно в нужную функцию, в которой обрабатывается"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'progress'
    command = db.get_user_parameter(user_id, section)

    try:
        await globals()[command](message)

    except Exception as error:
        print(error)
        await message.answer(template_messages.not_correct_message)


if __name__ == '__main__':
    executor.start_polling(dp)
