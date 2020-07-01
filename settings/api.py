from pyowm import OWM  # API для работы с погодой
from newsapi import NewsApiClient  # API для работы с новостями

from datetime import datetime, timedelta
from dateutil.parser import parse

from settings import config  # Модуль, в котором хранятся Токены от API, "security" информация
from settings import template_messages  # Модуль, в котором хранятся большие, повторяющиеся сообщения

owm = OWM(config.OWM_TOKEN, language='ru')

# У news api ограничение - 500 запросов в день. Есть 2 токена, в чётные часы используется один, в нечётные - другой
if int(datetime.today().strftime('%H')) % 2 == 0:
    news_api_key_index = 0
else:
    news_api_key_index = 1

news_api = NewsApiClient(api_key=config.NEWS_TOKEN[news_api_key_index])


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
        time_published = all_articles["articles"][news_number]["publishedAt"]
        time_published = parse(time_published)

        message = f'✔<b>Дата публикации: </b><i>{time_published.strftime("%d.%m.%Y")}</i>\n' \
                  f'✔<b>Заголовок: </b><i>{all_articles["articles"][news_number]["title"]}</i>\n' \
                  f'✔<b>Ссылка: </b><i>{all_articles["articles"][news_number]["url"]}</i>'

    except IndexError:
        if news_number > 0:
            message = f'🧐К сожалению, больше новостей по теме <b>"{news_topic}"</b> не найдено. Удалось найти ' \
                      f'только <b>{news_number+1}</b> новости(ей) из <b>{quantity_news}</b>🙁.\n' \
                      f'Если вы хотите получить больше новостей, попробуйте повторить попытку чуть позже, либо ' \
                      f'введите команду <b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будете получать получать их😉'

        else:
            message = f'🧐Новостей по теме <b>"{news_topic}"</b> не найдено. ' \
                      f'Вы можете повторить попытку чуть позже, либо ввести ' \
                      f'команду <b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будете получать новости😉'

    return message
