import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import quote_html
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from pyowm.exceptions import api_response_error  # Импортируем обработчик ошибок PYOWM API

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from data import db  # Модуль для работы с базой данных

from states.params import Params

from settings import config  # Модуль, в котором хранятся Токены от API, "секретная" информация
from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения
# Модуль, в котором генерируется ответ на запрос по смене параметра, параметр, если валиден, заносится в БД
from settings.changer_params import change_time, change_city, change_news_topic, change_status

from api.api import get_news, get_weather  # Модуль, который работает с API погоды, новостей


# Включаем логгирование
logging.basicConfig(level=logging.INFO)

# Инициализируем бота
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализируем, запускаем apscheduler (нужен для регулярной рассылки погоды и новостей)
scheduler = AsyncIOScheduler()
scheduler.start()


@dp.message_handler(commands='start')
@dp.throttled(rate=3)
async def send_welcome(message: types.Message):
    """Выводит приветственное соощение пользователю, активирует 'reply' клавиатуру"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.reply(f'<b>🤝Здравствуйте, {quote_html(message.from_user.first_name)}🤝!</b>')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    item1 = types.KeyboardButton('🧐Новости')
    item2 = types.KeyboardButton('🌤Погода')
    markup.add(item1, item2)
    await message.answer(template_messages.welcome_message, reply_markup=markup)


@dp.message_handler(commands='help')
@dp.throttled(rate=3)
async def show_information(message: types.Message):
    """Отправляет информацию о боте пользователю"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer(template_messages.information_message)


@dp.message_handler(text='🌤Погода')
@dp.throttled(rate=3)
async def send_weather(message: types.Message):
    """Отправляет погоду по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    section = 'city'
    city = db.get_user_parameter(user_id, section)
    try:
        weather = get_weather(city)
        await message.answer(weather)

    except api_response_error.NotFoundError:
        await message.answer('К сожалению, <b>произошла ошибка</b> во время подключения к серверу. Пожалуйста, '
                             'повтори попытку🤔')


@dp.message_handler(text='🧐Новости')
@dp.throttled(rate=3)
async def send_news(message: types.Message):
    """Отправляет новости по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

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
        await asyncio.sleep(1)
        news_number += 1


@dp.message_handler(commands='set_time')
@dp.throttled(rate=3)
async def set_time(message: types.Message):
    """Изменяет время регулярной отправки погоды и новостей"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer('Введи время <b>(по МСК)</b>, в которое каждый день будешь получать '
                         'новости и сводку погоды. Формат: <b>ЧЧ:ММ</b>. Примеры: '
                         '<b>08:20</b>, <b>22:05</b>')

    await Params.SetTime.set()


@dp.message_handler(state=Params.SetTime)
async def setting_time_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_time = message.text

    message_to_user = change_time(user_id, new_time)
    await message.answer(message_to_user)

    await state.finish()


@dp.message_handler(commands='set_city')
@dp.throttled(rate=3)
async def set_city(message: types.Message):
    """Изменяет город, из которого пользователь будет получать сводку погоды"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer('Введи город, из которого хочешь получать сводку погоды.\nПримеры: '
                         '<b>Санкт-Петербург</b>, <b>Киев</b>, <b>Брянск</b>')

    await Params.SetCity.set()


@dp.message_handler(state=Params.SetCity)
async def setting_city_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    new_city = message.text
    message_to_user = change_city(user_id, new_city)
    await message.answer(message_to_user)

    await state.finish()


@dp.message_handler(commands='set_news_topic')
@dp.throttled(rate=3)
async def set_news_topic(message: types.Message):
    """Изменяет ключевое слово, по которому отбираются новости"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer('Введите ключевое слово (фразу), по которому(ой) ты будешь получать новости.\n'
                         'Примеры: <b>Apple</b>, <b>Бизнес</b>, <b>Павел Дуров</b>\n\n'
                         '<b>P.S.</b> <i>Если хочешь получать самые актуальные зарубежные новости, введи '
                         'ключевое слово (фразу) на иностранном языке</i>')

    await Params.SetNewsTopic.set()


@dp.message_handler(state=Params.SetNewsTopic)
async def setting_news_topic_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    new_news_topic = message.text
    message_to_user = change_news_topic(user_id, new_news_topic)
    await message.answer(message_to_user)

    await state.finish()


@dp.message_handler(commands='reset')
@dp.throttled(rate=3)
async def reset_settings(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    time_registered = db.get_user_parameter(user_id, 'time_registered')

    db.delete_user_info(user_id)
    await message.answer('✔<i>Старые настройки успешно удалены!</i>\n'
                         '✔<i>Новые настройки успешно установлены!</i>\n\n'
                         '<b>Теперь, ты будешь ежедневно получать одну новость по ключевому слову "Россия" '
                         'и погоду из Москвы в 08:00 по МСК</b>')

    db.add_new_user(user_id, user_name)
    db.change_user_parameter(user_id, 'time_registered', time_registered)


@dp.message_handler(commands='set_status')
@dp.throttled(rate=3)
async def set_status(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    message_to_user = change_status(user_id)
    await message.answer(message_to_user)


@dp.message_handler(commands='set_quantity_news')
@dp.throttled(rate=3)
async def set_quantity_news_buttons(message: types.Message):
    """Изменяет количество новостей, которое будет получать пользователь"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

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

    await message.answer('Выбери количество новостей, которое будешь получать. Если не хочешь изменять значение, '
                         'нажми на кнопку <b>Отмена</b>', reply_markup=markup)


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

        message_to_user += f'✔Теперь, ты будете получать новости в количестве <b>{callback_data}</b> за раз!'
        await call.message.answer(message_to_user)

    else:
        await call.message.answer(f'<b>Действие успешно отменено</b>, скрываю клавиатуру😃')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(commands='donate')
@dp.throttled(rate=3)
async def donate_buttons(message: types.Message):
    """Отправлят кнопки"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="QIWI", url='qiwi.com/n/ANDRUS', callback_data='donate_QIWI')],
            [types.InlineKeyboardButton(text="Номер карты (Сбербанк)", callback_data='donate_Sberbank')],
            [types.InlineKeyboardButton(text="Отмена", callback_data='donate_cancel')]
        ]
    )

    await message.answer('Выбери способ оплаты. Если хочешь поддержать проект через <b>QIWI</b>, '
                         'после перевода средств нажми <b>Отмена</b>, иначе кнопки не пропадут')
    await message.answer('<b>Если действительно хочешь задонатить, пожалуйста, укажи в сообщении с донатом ссылку '
                         'на свой телеграмм-аккаунт, чтобы создатель бота смог написать и поблагодарить '
                         'тебя😉</b>', reply_markup=markup)


@dp.callback_query_handler(text_contains='donate_')
async def donation(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = str(call.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await call.answer(cache_time=10)

    callback_data = str(call.data).replace('donate_', '')

    if callback_data == 'Sberbank':
        await call.message.answer(f'Номер карты (Сбербанк): <b>{config.CARD_NUMBER} -- <i>{config.MY_NAME}</i></b>')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(commands='check_params')
@dp.throttled(rate=3)
async def check_params(message: types.Message):
    """Отправляет текущие настройки пользователя"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    user_params = db.get_all_user_info(user_id)
    await message.answer(f'Отправляю твои текущие настройки:\n\n{user_params}\n\nЕсли хочешь изменить что-либо, '
                         f'воспользуйся остальными командами!😃')


@dp.message_handler()
async def message_control(message: types.Message):
    """Возвращает сообщение о неправильном вводе информации"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    db.add_new_user(user_id, user_name)

    await message.answer(template_messages.not_correct_message)


def get_user_params(user):
    """Возвращает словарь с данными о пользователе"""
    user_params = {'id': user[0],
                   'name': user[1],
                   'send_time': user[2],
                   'city': user[3],
                   'news_topic': user[4],
                   'quantity_news': user[5],
                   'status': user[6]
                   }
    return user_params


async def user_regular_sending(user_params):
    """Получает параметры подписанного на рассылку пользователя, отправляет ему новости и погоду"""
    # Работа с новостями
    # Блок try нужен для того, чтобы бот не ломался при попытке отправке инфы пользователю, который
    # забанил бота
    try:
        for news_number in range(0, user_params['quantity_news']):
            news_message = get_news(user_params['news_topic'], user_params['quantity_news'], news_number)
            await bot.send_message(user_params['id'], news_message)

            # Если команда "/set_news_topic" в news_message - значит, было отправлено сообщение о том, что больше
            # новостей не найдено -> выход из цикла
            if '/set_news_topic' in news_message:
                break

        # Работа с погодой
        weather_message = get_weather(user_params['city'])
        await bot.send_message(user_params['id'], weather_message)

    except:
        pass


@scheduler.scheduled_job('cron', id='users_sending_control', second='0')
async def users_sending_control():
    # Получаем список кортежей со всеми пользователями
    all_users = db.get_all_users_info()

    for user in all_users:
        # Получаем словарь для более удобной работы
        user_params = get_user_params(user)

        # Проверяем, деактивирована ли подписка пользователя
        if user_params['status'] == 0:
            cron_obj = scheduler.get_job(job_id=str(user_params['id']))
            if cron_obj is not None:
                scheduler.remove_job(job_id=str(user_params['id']))

        # Сюда попадаем, если пользователь подписан на рассылку
        else:
            # Получаем объект cron
            cron_obj = scheduler.get_job(job_id=str(user_params['id']))

            # Получаем время пользователя из объекта крона
            from_db_time = user_params['send_time'].split(':')
            from_db_hours = int(from_db_time[0])
            from_db_minutes = int(from_db_time[1])

            if cron_obj is None:
                # Блок try нужен для того, чтобы бот не ломался при попытке отправке инфы пользователю, который
                # забанил бота
                scheduler.add_job(user_regular_sending,
                                  CronTrigger.from_crontab(f'{from_db_minutes} {from_db_hours} * * *'),
                                  args=(user_params,), id=str(user_params['id']))

            else:
                schedule_time = cron_obj.next_run_time.strftime('%H:%M')
                schedule_time = str(schedule_time).split(':')
                schedule_hours = int(schedule_time[0])
                schedule_minutes = int(schedule_time[1])

                # Проверяем, изменил ли пользователь настройки
                if schedule_hours != from_db_hours or schedule_minutes != from_db_minutes:
                    scheduler.remove_job(str(user_params['id']))
                    scheduler.add_job(user_regular_sending,
                                      CronTrigger.from_crontab(f'{from_db_minutes} {from_db_hours} * * *'),
                                      args=(user_params,), id=str(user_params['id']))


loop = asyncio.get_event_loop()

if __name__ == '__main__':
    executor.start_polling(dp, loop=loop)
