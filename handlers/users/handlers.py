import asyncio
import random

from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatType
from aiogram.utils.markdown import quote_html
from pyowm.exceptions import api_response_error

from api import currency_parser
from api.api import get_news, get_weather
from data import db, config
from keyboards.inline import user_keyboards
from keyboards.reply.default_keyboards import default_user_markup, default_group_markup
from loader import bot, dp, types
from settings.group_settings import group_template_messages as group_tmp_msg
from settings.user_settings import changer_user_params
from settings.user_settings import private_chat_template_messages as private_tmp_msg
from states.params import UserParams


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
