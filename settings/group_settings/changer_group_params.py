from newsapi import NewsApiClient  # API для работы с новостями

from datetime import datetime, timedelta

from settings import config  # Модуль, в котором хранятся Токены от API, "security" информация

from data import db  # Модуль для работы с базой данных


news_api = NewsApiClient(api_key=config.NEWS_TOKEN[0])


def change_time(group_id, new_hours: str):
    """Вспомогательная функция (основная - set_time), в которой происходит валидация введённого времени пользователем.
    Валидация пройдена -> значение в базу данных, иначе - соответствующее сообщение пользователю"""
    new_hours = new_hours.split(', ')
    formatted_hours = []
    no_added_hours = []

    for hour in new_hours:
        if hour.isdigit():
            try:
                hour = int(hour)
                if 0 <= hour <= 23:
                    if str(hour) not in formatted_hours:
                        formatted_hours.append(str(hour))
                else:
                    no_added_hours.append(str(hour))
            except ValueError:
                no_added_hours.append(str(hour))
        else:
            no_added_hours.append(str(hour))

    if len(formatted_hours) == 0:
        message = '❌Ни один час верно не указан. Изменения не приняты! Повторите попытку, перечитайте требования ' \
                  'ввода, если есть вопросы, задайте их в чате: <b>@andrus_news_chat</b>'

    else:
        if len(no_added_hours) == 0:
            message = '✔Все введённые часы указаны верно, изменения внесены в базу!'

        else:
            message = f'✔Верно указанные часы: <b>{", ".join(formatted_hours)}</b>\n' \
                      f'❌Неверно указанные часы: <b>{", ".join(no_added_hours)}</b>\n\n' \
                      f'Неверно указанные часы не добавлены в базу'

        section = 'send_hours'
        info = ', '.join(formatted_hours)
        db.change_group_parameter(group_id, section, info)

    return message


def change_news_topics(group_id, new_news_topics: str):
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

        min_quantity_news = 3

        if news['totalResults'] < min_quantity_news:
            no_added_news_topics.append(topic)
            new_news_topics.remove(topic)

    if len(new_news_topics) == 0:
        message = '❌Не удалось найти ни одной новости ни по одной из введёных тем. <b>Изменения не приняты</b>, ' \
                  'повторите попытку. Ещё раз перечитайте требование ввода. Если есть вопросы, задайте их в чате: ' \
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
        db.change_group_parameter(group_id, section, info)

    return message


def change_status(group_id):
    """Функция, изменяющая статус подписки группы (получать/не получать рассылку)"""
    section = 'status'
    old_status = db.get_group_parameter(group_id, section)

    if old_status == 1:
        message = '<b>Отмена подписки была успешно проведена</b>. Теперь, чат не будет получать ' \
                  'новостную рассылку, но <b>кнопка остаётся доступной</b>. В любой момент администраторы могут ' \
                  'востановить подписку на рассылку, введя эту же команду'

        parameter = 0
        db.change_user_parameter(group_id, section, parameter)

    else:
        message = '<b>Восстановление подписки было успешно проведено</b>. Теперь, ' \
                  'группа будет получать рассылку новостей'
        parameter = 1
        db.change_user_parameter(group_id, section, parameter)

    return message
