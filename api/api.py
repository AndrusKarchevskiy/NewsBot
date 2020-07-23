from datetime import datetime, timedelta

from dateutil.parser import parse
from newsapi import NewsApiClient  # API для работы с новостями
from pyowm import OWM  # API для работы с погодой

from data import config
from settings.user_settings import private_chat_template_messages as private_tmp_msg

owm = OWM(config.OWM_TOKEN, language='ru')

# У news api ограничение - 500 запросов в день. Есть несколько токенов, которые используются в разное время
hours = int(datetime.today().strftime('%H'))

if 0 <= hours <= 3:
    news_api_key_index = 1
elif 4 <= hours <= 6:
    news_api_key_index = 2
elif hours == 7:
    news_api_key_index = 3
elif hours == 8:
    news_api_key_index = 4
elif hours == 9:
    news_api_key_index = 5
elif 10 <= hours <= 11:
    news_api_key_index = 6
elif 12 <= hours <= 13:
    news_api_key_index = 7
elif 14 <= hours <= 15:
    news_api_key_index = 8
elif 16 <= hours <= 17:
    news_api_key_index = 9
elif 18 <= hours <= 20:
    news_api_key_index = 10
else:
    news_api_key_index = 11

news_api = NewsApiClient(api_key=config.NEWS_TOKEN[news_api_key_index])


def get_weather(city):
    """Работает с pyowm API, возвращает готовое сообщение с погодой"""
    observation = owm.weather_at_place(city)
    w = observation.get_weather()
    detailed_status = w.get_detailed_status()
    temp = str(w.get_temperature("celsius")["temp"])
    humidity = str(w.get_humidity())
    wind = str(w.get_wind()["speed"])

    if detailed_status in private_tmp_msg.weather_emoji:
        message = f'В городе <b>{city}</b> в ближайшее время будет <b>{detailed_status}</b>' \
                  f'{private_tmp_msg.weather_emoji[detailed_status]}'
    else:
        message = f'В городе <b>{city}</b> в ближайшее время будет <b>{detailed_status}</b>'

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

        message = f'✔<b>Дата публикации: </b><i>{time_published.strftime("%d.%m.%Y")}</i>\n\n' \
                  f'✔<b>Заголовок: </b><i>{all_articles["articles"][news_number]["title"]}</i>\n\n' \
                  f'✔<b>Ссылка: </b><i>{all_articles["articles"][news_number]["url"]}</i>'

    except IndexError:
        if news_number > 0:
            message = f'🧐К сожалению, больше новостей по теме <b>"{news_topic}"</b> не найдено. Удалось найти ' \
                      f'только <b>{news_number + 1}</b> новости(ей) из <b>{quantity_news}</b>🙁.\n' \
                      f'Если хочешь получить больше новостей, попробуй повторить попытку чуть позже, либо ' \
                      f'введи команду <b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будешь получать их😉'

        else:
            message = f'🧐Новостей по теме <b>"{news_topic}"</b> не найдено. ' \
                      f'Ты можешь повторить попытку чуть позже, либо ввести ' \
                      f'команду <b>/set_news_topic</b>, чтобы сменить ключевое ' \
                      f'слово, по которому будешь получать новости😉'

    return message
