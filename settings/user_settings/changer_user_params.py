from datetime import datetime, timedelta

from dateutil.parser import parse
from newsapi import NewsApiClient  # API для работы с новостями
from pyowm.exceptions import api_response_error  # Импортируем обработчик ошибок PYOWM API

from api import api  # Модуль для работы с API
from data import db, config  # Модуль для работы с базой данных
from settings.user_settings import private_chat_template_messages as private_tmp_msg

news_api = NewsApiClient(api_key=config.NEWS_TOKEN[0])


async def change_time(user_id, new_time):
    """Вспомогательная функция (основная - set_time), в которой происходит валидация введённого времени пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        section = 'send_time'
        old_time = await db.get_user_parameter(user_id, section)
        new_time = parse(new_time).strftime("%H:%M")
        message = f'✔Время <b>{old_time}</b> успешно удалено!😃\n'

        if old_time == new_time:
            message = f'Введено время, которое уже установлено - <b>{old_time}</b>. Если действительно ' \
                      f'хочешь изменить его, введи другое😃'
        else:
            parameter = new_time
            await db.change_user_parameter(user_id, section, parameter)
            message += f'✔Время <b>{new_time}</b> успешно установлено!😃'

    except Exception:
        message = private_tmp_msg.not_correct_param

    return message


async def change_city(user_id, new_city):
    """Вспомогательная функция (основная - set_city), в которой происходит валидация введённого города пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        new_city = new_city.title()

        api.get_weather(new_city)  # Пробуем получить данные из региона, введённого пользователем

        section = 'city'
        old_city = await db.get_user_parameter(user_id, section)

        if new_city == old_city:
            message = f'Введён город, который уже установлен - <b>{new_city}</b>. Если действительно хочешь изменить ' \
                      f'его, введи другой😃'

        else:
            message = f'✔Город <b>{old_city}</b> успешно удалён!😃\n'

            parameter = new_city
            await db.change_user_parameter(user_id, section, parameter)

            message += f'✔Город <b>{new_city}</b> успешно установлен!😃'

    except api_response_error.NotFoundError:
        message = private_tmp_msg.not_correct_param

    return message


async def change_news_topics(user_id, new_news_topics: str):
    """Функция, в которой происходит валидация введённой админом тем новостей.
     Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение в группу"""
    new_news_topics = new_news_topics.split(', ')
    no_added_news_topics = []

    today = datetime.today()
    today = today.strftime("%Y-%m-%d")

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")

    for topic in new_news_topics:
        news = news_api.get_everything(q=topic,
                                       from_param=yesterday,
                                       to=today,
                                       sort_by='relevancy')

        min_quantity_news = 5

        if news['totalResults'] < min_quantity_news:
            no_added_news_topics.append(topic)
            new_news_topics.remove(topic)

    if len(new_news_topics) == 0:
        message = '❌Не удалось найти ни одной новости ни по одной из введёных тем. <b>Изменения не приняты</b>, ' \
                  'повтори попытку. Ещё раз перечитай требование ввода. Если есть вопросы, задайте их в чате: ' \
                  '<b>@andrus_news_chat</b>'

    else:
        if len(no_added_news_topics) == 0:
            message = '✔Все темы новостей успешно занесены в базу!'
        else:
            message = f'✔Добавленные темы новостей: <b>{", ".join(new_news_topics)}</b>\n' \
                      f'❌Не найдены новости за последнее время по темам: <b>{", ".join(no_added_news_topics)}' \
                      f'</b>\n\n' \
                      f'Темы, по которым не удалось найти новостей за последнее время, добавлены в базу не будут.'

        section = 'news_topics'
        info = ", ".join(new_news_topics)
        await db.change_user_parameter(user_id, section, info)

    return message


async def change_status(user_id):
    """Функция, изменяющая статус подписки пользователя (получать/не получать рассылку)"""
    section = 'status'

    old_status = await db.get_user_parameter(user_id, section)

    if old_status == 1:
        message = '<b>Отмена подписки была успешно проведена</b>. Теперь, ты не ' \
                  'будешь получать новости, погоду в определённое время, но в ' \
                  'любой момент снова можешь подписаться, введя эту же команду😉'
        parameter = 0
        await db.change_user_parameter(user_id, section, parameter)

    else:
        message = '<b>Восстановление подписки было успешно проведено</b>. Теперь, ' \
                  'ты будешь получать рассылку новостей и погоды в выбранное тобой время😉'
        parameter = 1
        await db.change_user_parameter(user_id, section, parameter)

    return message
