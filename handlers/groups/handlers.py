import asyncio
import random

from aiogram.dispatcher import FSMContext
from aiogram.types.chat import ChatType

from api import currency_parser
from api.api import get_news
from data import db
from keyboards.inline import group_keyboards
from keyboards.reply.default_keyboards import default_group_markup
from loader import dp, types
from settings.group_settings import changer_group_params
from settings.group_settings import group_template_messages as group_tmp_msg
from states.params import GroupParams


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
