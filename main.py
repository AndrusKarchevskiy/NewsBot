import asyncio
import logging
import random

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatType
from aiogram.utils import exceptions
from aiogram.utils.markdown import quote_html

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pyowm.exceptions import api_response_error

from api.api import get_news, get_weather
from api import currency_parser

from data import db
from settings import config
from settings.user_settings import private_chat_template_messages as private_tmp_msg
from settings.group_settings import group_template_messages as group_tmp_msg
from settings.user_settings import changer_user_params
from settings.group_settings import changer_group_params
from states.params import UserParams, GroupParams

from keyboards.reply.default_keyboards import default_user_markup, default_group_markup
from keyboards.inline import user_keyboards, group_keyboards


# Включаем логгирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',)

# Инициализируем бота
bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Инициализируем, запускаем apscheduler (нужен для регулярной рассылки погоды и новостей)
scheduler = AsyncIOScheduler()
scheduler.start()


@dp.message_handler(ChatType.is_private, commands='start')
@dp.throttled(rate=3)
async def user_send_welcome(message: types.Message):
    """Выводит приветственное соощение пользователю, активирует 'reply' клавиатуру"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.reply(f'<b>🤝Здравствуйте, {quote_html(message.from_user.first_name)}🤝!</b>')

    await message.answer(private_tmp_msg.welcome_message, reply_markup=default_user_markup)


@dp.message_handler(ChatType.is_private, commands='help')
@dp.throttled(rate=3)
async def user_show_information(message: types.Message):
    """Отправляет информацию о боте пользователю"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer(private_tmp_msg.information_message, reply_markup=default_user_markup)


@dp.message_handler(ChatType.is_private, text='🌤Погода')
@dp.throttled(rate=3)
async def user_send_weather(message: types.Message):
    """Отправляет погоду по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    section = 'city'
    city = await db.get_user_parameter(user_id, section)
    try:
        weather = get_weather(city)
        await message.answer(weather, reply_markup=default_user_markup)

    except api_response_error.NotFoundError:
        await message.answer('К сожалению, <b>произошла ошибка</b> во время подключения к серверу. Пожалуйста, '
                             'повтори попытку🤔', reply_markup=default_user_markup)


@dp.message_handler(ChatType.is_private, text='👔Курсы валют')
@dp.throttled(rate=3)
async def user_send_valutes(message: types.Message):
    """Отправляет курсы валют по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    message_to_user = currency_parser.get_base_message()
    await message.answer(message_to_user, reply_markup=user_keyboards.currency_markup)


@dp.callback_query_handler(text_contains='more_details')
async def user_donation(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = call.from_user.full_name
    await db.add_new_user(user_id, user_name)

    message_to_user = currency_parser.get_detailed_message()
    await call.message.answer(message_to_user)
    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(ChatType.is_private, text='🧐Новости')
@dp.throttled(rate=3)
async def user_send_news(message: types.Message):
    """Отправляет новости по нажатию на кнопку"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    await db.add_new_user(user_id, user_name)

    section = 'news_topics'
    news_topics = await db.get_user_parameter(user_id, section)
    news_topics = news_topics.split(', ')

    section = 'quantity_news'
    quantity_news = await db.get_user_parameter(user_id, section)

    for news_number in range(quantity_news):
        news = get_news(random.choice(news_topics), quantity_news, news_number)
        await message.answer(news, reply_markup=default_user_markup)

        # Если команда "/set_news_topic" в news - значит, было отправлено сообщение о том, что больше новостей не
        # найдено -> выход из цикла
        if '/set_news_topic' in news:
            break
        await asyncio.sleep(1)


@dp.message_handler(ChatType.is_private, commands='set_time')
@dp.throttled(rate=3)
async def user_set_time(message: types.Message):
    """Изменяет время регулярной отправки погоды и новостей"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer('Введи время <b>(по МСК)</b>, в которое каждый день будешь получать '
                         'новости и сводку погоды. Формат: <b>ЧЧ:ММ</b>. Примеры: '
                         '<b>08:20</b>, <b>22:05</b>', reply_markup=default_user_markup)

    await UserParams.SetTime.set()


@dp.message_handler(state=UserParams.SetTime)
async def user_setting_time_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    new_time = message.text

    message_to_user = await changer_user_params.change_time(user_id, new_time)
    await message.answer(message_to_user, reply_markup=default_user_markup)

    await state.finish()


@dp.message_handler(ChatType.is_private, commands='set_city')
@dp.throttled(rate=3)
async def user_set_city(message: types.Message):
    """Изменяет город, из которого пользователь будет получать сводку погоды"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer('Введи город, из которого хочешь получать сводку погоды.\nПримеры: '
                         '<b>Санкт-Петербург</b>, <b>Киев</b>, <b>Брянск</b>', reply_markup=default_user_markup)

    await UserParams.SetCity.set()


@dp.message_handler(state=UserParams.SetCity)
async def user_setting_city_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    new_city = message.text
    message_to_user = await changer_user_params.change_city(user_id, new_city)
    await message.answer(message_to_user, reply_markup=default_user_markup)

    await state.finish()


@dp.message_handler(ChatType.is_private, commands='set_news_topic')
@dp.throttled(rate=3)
async def user_set_news_topic(message: types.Message):
    """Изменяет ключевое слово, по которому отбираются новости"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer('Введите ключевое слово (фразу), по которому(ой) ты будешь получать новости.\n'
                         'Примеры: <b>Apple</b>, <b>бизнес</b>, <b>экономика</b>\n\n'
                         '<b>P.S.</b> <i>Если хочешь получать самые актуальные зарубежные новости, введи '
                         'ключевое слово (фразу) на иностранном языке</i>', reply_markup=default_user_markup)

    await UserParams.SetNewsTopic.set()


@dp.message_handler(state=UserParams.SetNewsTopic)
async def user_setting_news_topic_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    new_news_topic = message.text
    message_to_user = await changer_user_params.change_news_topics(user_id, new_news_topic)
    await message.answer(message_to_user, reply_markup=default_user_markup)

    await state.finish()


@dp.message_handler(ChatType.is_private, commands='reset')
@dp.throttled(rate=3)
async def user_reset_settings(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    time_registered = await db.get_user_parameter(user_id, 'time_registered')

    await db.delete_user_info(user_id)
    await message.answer('✔<i>Старые настройки успешно удалены!</i>\n'
                         '✔<i>Новые настройки успешно установлены!</i>\n\n'
                         '<b>Теперь, ты будешь ежедневно получать одну новость по одной из одной тем: '
                         '<b>Россия, бизнес, экономика, игры, образование</b> '
                         'и погоду из Москвы в 08:00 по МСК</b>', reply_markup=default_user_markup)

    await db.add_new_user(user_id, user_name)
    await db.change_user_parameter(user_id, 'time_registered', time_registered)


@dp.message_handler(ChatType.is_private, commands='set_status')
@dp.throttled(rate=3)
async def user_set_status(message: types.Message):
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    message_to_user = await changer_user_params.change_status(user_id)
    await message.answer(message_to_user, reply_markup=default_user_markup)


@dp.message_handler(ChatType.is_private, commands='set_quantity_news')
@dp.throttled(rate=3)
async def user_set_quantity_news_buttons(message: types.Message):
    """Изменяет количество новостей, которое будет получать пользователь"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer('Выбери количество новостей, которое будешь получать. Если не хочешь изменять значение, '
                         'нажми на кнопку <b>Отмена</b>', reply_markup=user_keyboards.quantity_news_markup)


@dp.callback_query_handler(text_contains='private_chat_news_')
async def user_change_quantity_news(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = str(call.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await call.answer(cache_time=10)

    callback_data = str(call.data).replace('private_chat_news_', '')

    if callback_data.isdigit():
        section = 'quantity_news'
        old_quantity_news = await db.get_user_parameter(user_id, section)
        message_to_user = f'✔Количество новостей <b>{old_quantity_news}</b> успешно удалено!\n'

        parameter = callback_data
        await db.change_user_parameter(user_id, section, parameter)

        message_to_user += f'✔Теперь, ты будете получать новости в количестве <b>{callback_data}</b> за раз!'
        await call.message.answer(message_to_user)

    else:
        await call.message.answer(f'<b>Действие успешно отменено</b>, скрываю клавиатуру😃')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(ChatType.is_private, commands='donate')
@dp.throttled(rate=3)
async def user_donate_buttons(message: types.Message):
    """Отправлят кнопки"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer('Выбери способ оплаты. Если хочешь поддержать проект через <b>QIWI</b>, '
                         'после перевода средств нажми <b>Отмена</b>, иначе кнопки не пропадут')

    await message.answer('<b>Если действительно хочешь задонатить, пожалуйста, укажи в сообщении с донатом ссылку '
                         'на свой телеграмм-аккаунт, чтобы создатель бота смог написать и поблагодарить тебя😉</b>',
                         reply_markup=user_keyboards.donate_markup)


@dp.callback_query_handler(text_contains='private_chat_donate_')
async def user_donation(call: types.CallbackQuery):
    user_id = call.from_user.id
    user_name = str(call.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await call.answer(cache_time=10)

    callback_data = str(call.data).replace('private_chat_donate_', '')

    if callback_data == 'Sberbank':
        await call.message.answer(f'Номер карты (Сбербанк): <b>{config.CARD_NUMBER} -- <i>{config.MY_NAME}</i></b>')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(ChatType.is_private, commands='check_params')
@dp.throttled(rate=3)
async def check_user_params(message: types.Message):
    """Отправляет текущие настройки пользователя"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    user_params = await db.get_all_user_info(user_id)
    await message.answer(f'Отправляю твои текущие настройки:\n\n{user_params}\n\nЕсли хочешь изменить что-либо, '
                         f'воспользуйся остальными командами!😃', reply_markup=default_user_markup)


@dp.message_handler(ChatType.is_private)
async def user_message_control(message: types.Message):
    """Отправляет пользователю сообщение о неправильно введённой информации"""
    user_id = message.from_user.id
    user_name = str(message.from_user.full_name)
    await db.add_new_user(user_id, user_name)

    await message.answer(private_tmp_msg.not_correct_message, reply_markup=default_user_markup)


@dp.message_handler(content_types='new_chat_members')
async def adding_to_new_chat(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    for user in message.new_chat_members:
        if user.id == bot.id:
            await message.answer(group_tmp_msg.welcome_message, reply_markup=default_group_markup)
            break


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands=['start', 'help'])
@dp.throttled(rate=3)
async def show_information_to_group(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    await message.answer(group_tmp_msg.welcome_message, reply_markup=default_group_markup)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, text='🧐Новости')
@dp.throttled(rate=3)
async def group_send_news(message: types.Message):
    """Отправляет новости по нажатию на кнопку"""
    group_id = message.chat.id
    await db.add_new_group(group_id)

    section = 'news_topics'
    news_topics = await db.get_group_parameter(group_id, section)
    news_topics = news_topics.split(', ')

    section = 'quantity_news'
    quantity_news = await db.get_group_parameter(group_id, section)

    for news_number in range(quantity_news):
        news = get_news(random.choice(news_topics), quantity_news, news_number)
        await message.answer(news, reply_markup=default_group_markup)

        # Если команда "/set_news_topic" в news - значит, было отправлено сообщение о том, что больше новостей не
        # найдено -> выход из цикла
        if '/set_news_topic' in news:
            break
        await asyncio.sleep(1)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, text='👔Курсы валют')
@dp.throttled(rate=3)
async def group_send_valutes(message: types.Message):
    """Отправляет курсы валют по нажатию на кнопку"""
    group_id = message.chat.id
    await db.add_new_group(group_id)

    message_to_user = currency_parser.get_base_message() + '\n'
    message_to_user += currency_parser.get_detailed_message()
    await message.answer(message_to_user, reply_markup=default_group_markup)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='set_time')
@dp.throttled(rate=3)
async def set_group_time(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    await message.reply('Введите часы через запятую + пробел, в которые в чат автоматически будут отправляться '
                        'новости. Пример ввода: <b>8, 9, 12, 20</b>', reply_markup=default_group_markup)

    await GroupParams.SetHours.set()


@dp.message_handler(state=GroupParams.SetHours)
async def group_setting_time_handler(message: types.Message, state: FSMContext):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    new_time = message.text

    message_to_group = await changer_group_params.change_time(group_id, new_time)
    await message.reply(message_to_group, reply_markup=default_group_markup)

    await state.finish()


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='set_news_topic')
async def group_set_news_topics(message: types.Message):
    """Изменяет ключевые слово, по которым отбираются новости"""
    group_id = message.chat.id
    await db.add_new_group(group_id)

    await message.reply('Введите через запятую + пробел темы новостей, по которым группа будет получать новости.\n'
                        'Пример: <i>Россия, экономика, бизнес, футбол</i>', reply_markup=default_group_markup)

    await GroupParams.SetNewsTopics.set()


@dp.message_handler(state=GroupParams.SetNewsTopics)
async def group_setting_news_topics_handler(message: types.Message, state: FSMContext):
    group_id = message.chat.id
    new_news_topics = message.text

    message_to_group = await changer_group_params.change_news_topics(group_id, new_news_topics)
    await message.reply(message_to_group, reply_markup=default_group_markup)

    await state.finish()


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='set_quantity_news')
@dp.throttled(rate=3)
async def group_set_quantity_news_buttons(message: types.Message):
    """Отображает сообщение с кнопками"""
    group_id = message.chat.id
    await db.add_new_group(group_id)

    await message.answer('Выбери количество новостей, которое будет получать группа. Админ, если передумал '
                         'изменять значение, нажми на кнопку <b>Отмена</b>',
                         reply_markup=group_keyboards.quantity_news_markup)


@dp.callback_query_handler(is_chat_admin=True, text_contains='group_news_')
async def group_change_quantity_news(call: types.CallbackQuery):
    group_id = call.message.chat.id
    await db.add_new_group(group_id)

    callback_data = str(call.data).replace('group_news_', '')

    if callback_data.isdigit():
        section = 'quantity_news'

        parameter = callback_data
        await db.change_group_parameter(group_id, section, parameter)

        message_to_chat = f'✔Теперь, чат будете получать новости в количестве <b>{callback_data}</b> за раз!'
        await call.message.answer(message_to_chat)

    else:
        await call.message.answer(f'<b>Действие успешно отменено</b>, скрываю клавиатуру😃')

    await call.message.edit_reply_markup(reply_markup=None)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='set_status')
@dp.throttled(rate=3)
async def group_set_status(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    message_to_group = await changer_group_params.change_status(group_id)
    await message.reply(message_to_group, reply_markup=default_group_markup)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='check_params')
@dp.throttled(rate=3)
async def check_group_params(message: types.Message):
    """Отправляет текущие настройки пользователя"""
    group_id = message.chat.id
    await db.add_new_group(group_id)

    user_params = await db.get_all_group_info(group_id)
    await message.answer(f'Отправляю текущие настройки группы:\n\n{user_params}')


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands='reset')
@dp.throttled(rate=3)
async def user_reset_settings(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    time_added = await db.get_group_parameter(group_id, 'time_added')

    await db.delete_group_info(group_id)

    await message.answer('✔<i>Старые настройки успешно удалены!</i>\n'
                         '✔<i>Новые настройки успешно установлены!</i>\n\n'
                         '✔<i>Чтобы увидеть параметры, введите команду /check_params</i>',
                         reply_markup=default_group_markup)

    await db.add_new_group(group_id)
    await db.change_group_parameter(group_id, 'time_added', time_added)


@dp.message_handler(ChatType.is_group_or_super_group, is_chat_admin=True, commands=['set_city', 'donate'])
@dp.throttled(rate=5)
async def private_chat_command(message: types.Message):
    group_id = message.chat.id
    await db.add_new_group(group_id)

    await message.reply('<b>Команда доступна только в ЛС</b>', reply_markup=default_group_markup)


def get_user_params(user):
    """Возвращает словарь с данными о пользователе"""
    user_params = {'id': user[0],
                   'name': user[1],
                   'send_time': user[2],
                   'city': user[3],
                   'news_topics': user[4],
                   'quantity_news': user[5],
                   'status': user[6]
                   }
    return user_params


async def user_send_regular_info(user_params):
    """Получает параметры подписанного на рассылку пользователя, отправляет ему новости и погоду"""
    try:
        news_topics = user_params['news_topics']
        news_topics = news_topics.split(', ')

        for news_number in range(user_params['quantity_news']):
            news_message = get_news(random.choice(news_topics), user_params['quantity_news'], news_number)

            await bot.send_message(user_params['id'], news_message)

            # Если команда "/set_news_topic" в news_message - значит, было отправлено сообщение о том, что больше
            # новостей не найдено -> выход из цикла
            if '/set_news_topic' in news_message:
                break

        await asyncio.sleep(1)

        valutes_message = currency_parser.get_base_message()
        await bot.send_message(user_params['id'], valutes_message)
        await asyncio.sleep(1)

        weather_message = get_weather(user_params['city'])
        await bot.send_message(user_params['id'], weather_message, reply_markup=default_user_markup)

    except exceptions.BotBlocked:
        pass


@scheduler.scheduled_job('cron', id='users_sending_control', second='0')
async def controlling_users_sending():
    """Управляет пользовательскими объектами крона"""
    # Получаем список кортежей со всеми пользователями
    all_users = await db.get_all_users_info()

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
                scheduler.add_job(user_send_regular_info,
                                  CronTrigger.from_crontab(f'{from_db_minutes} {from_db_hours} * * *'),
                                  args=(user_params,), id=str(user_params['id']))

            else:
                schedule_time = cron_obj.next_run_time.strftime('%H:%M')
                schedule_time = str(schedule_time).split(':')
                schedule_hours = int(schedule_time[0])
                schedule_minutes = int(schedule_time[1])

                # Проверяем, изменил ли пользователь время отправки
                if schedule_hours != from_db_hours or schedule_minutes != from_db_minutes:
                    scheduler.remove_job(str(user_params['id']))
                    scheduler.add_job(user_send_regular_info,
                                      CronTrigger.from_crontab(f'{from_db_minutes} {from_db_hours} * * *'),
                                      args=(user_params,), id=str(user_params['id']))

        await asyncio.sleep(0.2)


def get_group_params(group):
    """Возвращает словарь с данными о пользователе"""
    group_params = {'id': group[0],
                    'news_topics': group[1],
                    'send_hours': group[2],
                    'quantity_news': group[3],
                    'status': group[4]
                    }
    return group_params


async def group_regular_sending(group_params):
    """Получает параметры группы, отправляет туда новости"""
    try:
        news_topics = group_params['news_topics']
        news_topics = news_topics.split(', ')

        for news_number in range(group_params['quantity_news']):
            news_message = get_news(random.choice(news_topics), group_params['quantity_news'], news_number)
            await bot.send_message(group_params['id'], news_message)
            await asyncio.sleep(1)

        valutes_message = currency_parser.get_base_message() + '\n'
        valutes_message += currency_parser.get_detailed_message()
        await bot.send_message(group_params['id'], valutes_message, reply_markup=default_group_markup)

    except exceptions.BotBlocked:
        pass


@scheduler.scheduled_job(CronTrigger.from_crontab('0 * * * *'))
async def groups_sending_control():
    # Get list of tuples with all groups
    all_groups = await db.get_all_groups_info()

    for group in all_groups:
        group_params = get_group_params(group)

        cron_obj = scheduler.get_job(job_id=str(group_params['id']))

        if cron_obj is not None:
            scheduler.remove_job(job_id=str(group_params['id']))

        if group_params['status'] == 1:
            from_db_hours = group_params['send_hours']
            from_db_hours = from_db_hours.split(', ')
            from_db_hours = ','.join(from_db_hours)

            scheduler.add_job(group_regular_sending,
                              CronTrigger.from_crontab(f'{str(random.randint(1, 3))} {from_db_hours} * * *'),
                              args=(group_params,), id=str(group_params['id']))


loop = asyncio.get_event_loop()


if __name__ == '__main__':
    executor.start_polling(dp, loop=loop)
