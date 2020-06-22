import logging

from aiogram import Bot, Dispatcher, executor, types

from pyowm import OWM  # API для работы с погодой
from newsapi import NewsApiClient  # API для работы с новостями

import time
from datetime import datetime, timedelta
from dateutil.parser import parse

from data import db  # Модуль для работы с базой данных
from settings import keys  # Модуль, в котором хранятся Токены от API, "security" информация
from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения

logging.basicConfig(level=logging.INFO)

owm = OWM(keys.OWM_TOKEN, language='ru')
news_api = NewsApiClient(api_key=keys.NEWS_TOKEN)

bot = Bot(token=keys.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
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
    message += '\n<i>(P.S. В городах с населением менее миллиона, могут быть неточности с определением этого статуса, '\
               'не серчайте😉. Остальная информация - точная)</i>'

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
        time_published = all_articles["articles"][news_number]["publishedAt"]

        message = f'<b>Дата публикации: ' \
                  f'{parse(time_published).strftime("%d.%m.%Y")}</b>\n' \
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


def get_all_user_info(user_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    user_info = db.get_all_user_parameters(user_id)
    user_send_time = user_info[2]
    user_city = user_info[3]
    user_news_topic = user_info[4]
    user_quantity_news = user_info[5]
    user_status = user_info[6]

    message = f'✔Время, в которое вы получаете новости и погоду: <b>{user_send_time}</b>\n' \
              f'✔Город, из которого вы получате сводку погоды: <b>{user_city}</b>\n' \
              f'✔Ключевое слово (фраза), по которой вы получаете новости: <b>{user_news_topic}</b>\n' \
              f'✔Количество новостей, которое вы получаете: <b>{user_quantity_news}</b>\n'

    if user_status == 1:
        message += '✔Активна ли ваша подписка (получаете ли вы регулярную рассылку погоды и новостей): <b>Да</b>'
    else:
        message += '✔Активна ли ваша подписка (получаете ли вы регулярную рассылку погоды и новостей): <b>Нет</b>'

    return message


def change_time(user_id, new_time):
    """Вспомогательная функция (основная - set_time), в которой происходит валидация введённого времени пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        section = 'send_time'
        old_time = db.get_user_parameter(user_id, section)
        message = f'✔Время <b>{old_time}</b> успешно удалено!😃\n'

        new_time = parse(new_time).strftime("%H:%M")
        parameter = new_time
        db.change_user_parameter(user_id, section, parameter)
        message += f'✔Время <b>{new_time}</b> успешно установлено!😃'

    except Exception as error:
        print(error)
        message = template_messages.not_correct_param

    return message


def change_city(user_id, new_city):
    """Вспомогательная функция (основная - set_city), в которой происходит валидация введённого города пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        new_city = new_city.title()
        owm.weather_at_place(new_city)  # Пробуем получить данные из региона, введённого пользователем

        section = 'city'
        old_city = db.get_user_parameter(user_id, section)
        message = f'✔Город <b>{old_city}</b> успешно удалён!😃\n'

        parameter = new_city
        db.change_user_parameter(user_id, section, parameter)

        message += f'✔Город <b>{new_city}</b> успешно установлен!😃'

    except Exception as error:
        print(error)
        message = template_messages.not_correct_param

    return message


def change_news_topic(user_id, new_news_topic):
    """Вспомогательная функция (основная - set_news_topic), в которой происходит валидация введённой пользователем
    темы новостей. Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    today = datetime.today()
    today = today.strftime("%Y-%m-%d")

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")

    news = news_api.get_everything(q=new_news_topic,
                                   from_param=yesterday,
                                   to=today,
                                   sort_by='relevancy')

    min_quantity_news = 5

    if news['totalResults'] >= min_quantity_news:
        section = 'news_topic'
        old_news_topic = db.get_user_parameter(user_id, section)
        message = f'✔Тема (ключевое слово) <b>"{old_news_topic}"</b> успешно удалено(а)!😃\n'

        db.change_user_parameter(user_id, section, new_news_topic)
        message += f'✔Тема (ключевое слово) <b>"{new_news_topic}"</b> успешно установлено(а)!😃\n'

    else:
        message = 'Мне не удалось найти новостей по вашей теме за последние 2 дня. А мне хочется, ' \
                  'чтобы вы получали только самую актуальную информацию. Поэтому, <b>изменение не принято</b>, ' \
                  'выберете другую тему (ключевое слово)'

    return message


def change_status(user_id):
    section = 'status'

    old_status = db.get_user_parameter(user_id, section)

    if old_status == 1:
        message = '<b>Отмена подписки была успешно проведена</b>. Теперь, вы не ' \
                  'будете получать новости, погоду в определённое время, но в ' \
                  'любой момент снова можете подписаться, введя эту же команду😉'
        parameter = 0
        db.change_user_parameter(user_id, section, parameter)

    else:
        message = '<b>Восстановление подписки было успешно проведено</b>. Теперь, ' \
                  'вы будете получать новости и погоду в выбранное вами время😉'
        parameter = 1
        db.change_user_parameter(user_id, section, parameter)

    return message


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
    await message.answer('✔Старые настройки успешно удалены!\n'
                         '✔Новые настройки успешно установлены!\n\n'
                         'Теперь, вы будете ежедневно получать одну новость по ключевому слову <b>Россия</b> '
                         'и погоду из Москвы в 08:00 по МСК')

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
