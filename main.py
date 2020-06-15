import logging

from aiogram import Bot, Dispatcher, executor, types

from pyowm import OWM  # API для работы с погодой
from newsapi import NewsApiClient  # API для работы с новостями

import time
from datetime import datetime, timedelta
from dateutil.parser import parse

from data import db  # Модуль для работы с базой данных
from settings import keys  # Модуль, в котором хранятся Токены от API
from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения

logging.basicConfig(level=logging.INFO)

owm = OWM(keys.OWM_TOKEN, language='ru')
news_api = NewsApiClient(api_key=keys.NEWS_TOKEN)

bot = Bot(token=keys.BOT_TOKEN)
dp = Dispatcher(bot)


def get_weather(city):
    """Работает с pyowm API, возвращает готовое сообщение с погодой"""
    observation = owm.weather_at_place(city)
    w = observation.get_weather()
    detailed_status = w.get_detailed_status()
    temp = str(w.get_temperature("celsius")["temp"])
    humidity = str(w.get_humidity())
    wind = str(w.get_wind()["speed"])

    if detailed_status in template_messages.weather_emoji:
        message = f'В городе <b>{city}</b> сейчас <b>{detailed_status}</b>' \
                   f'{template_messages.weather_emoji[detailed_status]}'
    else:
        message = f'В городе <b>{city}</b> сейчас <b>{detailed_status}</b>'

    message += f'\n\n' \
               f'🌡Температура: <b>{temp} градус(ов)</b>\n' \
               f'💨Скорость ветра: <b>{wind} м/с</b>\n' \
               f'💦Влажность: <b>{humidity}%</b>'

    return message


def get_news(news_topic, quantity_news, news_number):
    """Работает с news API, возвращает сообщение с новостью"""
    today = datetime.today()
    today = today.strftime("%Y-%m-%d")

    all_articles = news_api.get_everything(q=news_topic,
                                           from_param=today,
                                           to=today,
                                           sort_by='relevancy')

    max_news = 5
    if len(all_articles["articles"]) < max_news:
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime("%Y-%m-%d")

        all_articles = news_api.get_everything(q=news_topic,
                                               from_param=yesterday,
                                               to=today,
                                               sort_by='relevancy')

    try:
        message = f'<b>Дата публикации: ' \
                  f'{parse(all_articles["articles"][news_number]["publishedAt"]).strftime("%d.%m.%Y")}</b>\n' \
                  f'✔{all_articles["articles"][news_number]["url"]}'

    except IndexError:
        if news_number > 0:
            message = f'🧐К сожалению, больше новостей по теме <b>"{news_topic}"</b> не найдено. Удалось найти ' \
                      f'только <b>{news_number+1}</b> новости(ей) из <b>{quantity_news}</b>🙁.\n' \
                      f'Если вы хотите получить больше новостей, попробуйте повторить попытку чуть позже, либо ' \
                      f'введите команду \n<b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будете получать новости😉'
        else:
            message = f'🧐Новостей по теме <b>"{news_topic}"</b> не найдено. ' \
                      f'Вы можете повторить попытку чуть позже, либо ввести ' \
                      f'команду \n<b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будете получать новости😉'

    return message


def change_time(user_id, new_time):
    """Вспомогательная функция (основная - set_time), в которой происходит валидация введённого времени пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        section = 'send_time'
        old_time = db.get_user_parameter(user_id, section)

        message = f'Время <b>{old_time}</b> успешно удалено!😃\n'
        new_time = parse(new_time).strftime("%H:%M")

        parameter = new_time
        db.change_user_parameter(user_id, section, parameter)

        message += f'Время <b>{new_time}</b> успешно установлено!😃'

    except Exception as error:
        print(error)
        message = template_messages.not_correct_param

    return message


def change_city(user_id, new_city):
    """Вспомогательная функция (основная - set_city), в которой происходит валидация введённого города пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        new_city = new_city.capitalize()

        owm.weather_at_place(new_city)

        section = 'city'
        old_city = db.get_user_parameter(user_id, section)

        message = f'Город <b>{old_city}</b> успешно удалён!😃\n'

        parameter = new_city
        db.change_user_parameter(user_id, section, parameter)

        message += f'Город <b>{new_city}</b> успешно установлен!😃'

    except Exception as error:
        print(error)
        message = template_messages.not_correct_param

    return message


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """Выводит приветственное соощение пользователю, активирует 'reply' клавиатуру"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    await message.reply('<b>🤝Здравствуйте, {0.first_name}🤝!</b>'.format(message.from_user), parse_mode='html')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item1 = types.KeyboardButton('🌤Погода')
    item2 = types.KeyboardButton('🧐Новости')

    markup.add(item1, item2)

    await message.answer(template_messages.welcome_message, parse_mode='html', reply_markup=markup)


@dp.message_handler(commands=['help'])
async def show_information(message: types.Message):
    """Отправляет информацию о боте пользователю"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    await message.answer(template_messages.information_message, parse_mode='html')


@dp.message_handler(regexp='🌤Погода')
async def send_weather(message: types.Message):
    """Отправляет погоду по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'b_weather'
    db.change_user_parameter(user_id, section, parameter)

    section = 'city'
    city = db.get_user_parameter(user_id, section)

    try:
        weather = get_weather(city)
        await message.answer(weather, parse_mode='html')

    except Exception as error:
        print(error)
        await message.answer('🤔К сожалению, <b>произошла ошибка</b> во время подключения к серверу. Пожалуйста, '
                             'повторите попытку', parse_mode='html')


@dp.message_handler(regexp='🧐Новости')
async def send_news(message: types.Message):
    """Отправляет новости по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

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

        await message.answer(news, parse_mode='html')

        # Если команда "/set_news_topic" в news - значит, больше новостей не найдено -> выход из цикла
        if '/set_news_topic' in news:
            break

        time.sleep(1)
        news_number += 1


@dp.message_handler(commands='set_time')
async def set_time(message: types.Message):
    """Изменяет время регулярной отправки погоды и новостей"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_time'
    db.change_user_parameter(user_id, section, parameter)

    if message.text == '/set_time':
        await message.answer('Введите время (по МСК), в которое вы каждый день будете получать '
                             'новости и сводку погоды. Формат: <b>ЧЧ:ММ</b>. Примеры: '
                             '<b>08:20</b>, <b>22:05</b>', parse_mode='html')

    else:
        new_time = message.text
        message_to_user = change_time(user_id, new_time)

        await message.answer(message_to_user, parse_mode='html')


@dp.message_handler(commands='set_city')
async def set_city(message: types.Message):
    """Изменяет город, из которого пользователь будет получать сводку погоды"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    section = 'progress'
    parameter = 'set_city'
    db.change_user_parameter(user_id, section, parameter)

    if message.text == '/set_city':
        await message.answer('Введите город, из которого хотите получать сводку погоды. Примеры: '
                             '<b>Санкт-Петербург</b>, <b>Киев</b>, <b>Брянск</b>', parse_mode='html')

    else:
        new_city = message.text
        message_to_user = change_city(user_id, new_city)

        await message.answer(message_to_user, parse_mode='html')


@dp.message_handler()
async def echo_message(message: types.Message):
    """Обрабатывает все текстовые сообщения. В функции, при вводе значений после ввода команды,
    значение отправляется обратно в нужную функцию, в которой обрабатывается"""
    user_id = message.from_user.id
    user_name = str(message.from_user.first_name) + ' ' + str(message.from_user.last_name)

    db.add_new_user(user_id, user_name)

    section = 'progress'
    command = db.get_user_parameter(user_id, section)

    try:
        await globals()[command](message)

    except Exception as error:
        print(error)
        await message.answer(template_messages.not_correct_message, parse_mode='html')


if __name__ == '__main__':
    executor.start_polling(dp)
