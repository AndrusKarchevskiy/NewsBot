from datetime import datetime, timedelta
from dateutil.parser import parse

from pyowm import OWM  # API для работы с погодой
from newsapi import NewsApiClient  # API для работы с новостями

from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения
from settings import config  # Модуль, в котором хранятся Токены от API, "security" информация

from data import db  # Модуль для работы с базой данных


owm = OWM(config.OWM_TOKEN, language='ru')
news_api = NewsApiClient(api_key=config.NEWS_TOKEN[0])


def change_time(user_id, new_time):
    """Вспомогательная функция (основная - set_time), в которой происходит валидация введённого времени пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    try:
        section = 'send_time'
        old_time = db.get_user_parameter(user_id, section)
        new_time = parse(new_time).strftime("%H:%M")
        message = f'✔Время <b>{old_time}</b> успешно удалено!😃\n'

        if old_time == new_time:
            message = f'Введено время, которое уже установлено - <b>{old_time}</b>. Если действительно ' \
                      f'хочешь изменить его, введи другое😃'
        else:
            parameter = new_time
            db.change_user_parameter(user_id, section, parameter)
            message += f'✔Время <b>{new_time}</b> успешно установлено!😃'

    except Exception:
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

        if new_city == old_city:
            message = f'Введён город, который уже установлен - <b>{new_city}</b>. Если действительно хочешь изменить ' \
                      f'его, введи другой😃'

        else:
            message = f'✔Город <b>{old_city}</b> успешно удалён!😃\n'

            parameter = new_city
            db.change_user_parameter(user_id, section, parameter)

            message += f'✔Город <b>{new_city}</b> успешно установлен!😃'

    except Exception:
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

        if old_news_topic == new_news_topic:
            message = f'Введена тема новостей, которая уже установлена - <b>{old_news_topic}</b>. Если действительно ' \
                      f'хочешь изменить её, введи другую😃'

        else:
            message = f'✔Тема (ключевое слово) <b>"{old_news_topic}"</b> успешно удалено(а)!😃\n'

            db.change_user_parameter(user_id, section, new_news_topic)
            message += f'✔Тема (ключевое слово) <b>"{new_news_topic}"</b> успешно установлено(а)!😃\n'

    else:
        message = '😕Мне не удалось найти новостей по введённой тобой теме за последние 2 дня. А я хочу ' \
                  'сообщать тебе только самую актуальную информацию😉. Поэтому, <b>изменение не принято</b>. ' \
                  'Пожалуйста, введи другую тему (ключевое слово)'

    return message


def change_status(user_id):
    """Функция, изменяющая статус подписки пользователя (получать/не получать рассылку)"""
    section = 'status'

    old_status = db.get_user_parameter(user_id, section)

    if old_status == 1:
        message = '<b>Отмена подписки была успешно проведена</b>. Теперь, ты не ' \
                  'будешь получать новости, погоду в определённое время, но в ' \
                  'любой момент снова можешь подписаться, введя эту же команду😉'
        parameter = 0
        db.change_user_parameter(user_id, section, parameter)

    else:
        message = '<b>Восстановление подписки было успешно проведено</b>. Теперь, ' \
                  'ты будешь получать рассылку новостей и погоды в выбранное тобой время😉'
        parameter = 1
        db.change_user_parameter(user_id, section, parameter)

    return message
