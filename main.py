import asyncio
import logging
import random

from aiogram.utils import exceptions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api import currency_parser
from api.api import get_news, get_weather
from data import db
from keyboards.reply.default_keyboards import default_user_markup, default_group_markup
from loader import bot

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', )

# Инициализируем, запускаем apscheduler (нужен для регулярной рассылки)
scheduler = AsyncIOScheduler()
scheduler.start()


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
    from aiogram import executor
    from handlers import dp

    executor.start_polling(dp, loop=loop)
