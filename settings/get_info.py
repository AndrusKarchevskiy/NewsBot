from data import db


def get_all_user_info(user_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    user_info = db.get_all_user_parameters(user_id)
    user_send_time = user_info[2]
    user_city = user_info[3]
    user_news_topic = user_info[4]
    user_quantity_news = user_info[5]
    user_status = user_info[6]

    message = f'✔Время, в которое вы получаете новости и погоду: <b>{user_send_time}</b>\n' \
              f'✔Город, из которого вы получате сводку погоды: <b>{user_city}</b>\n' \
              f'✔Ключевое слово (фраза), по которой вы получаете новости: <b>{user_news_topic}</b>\n' \
              f'✔Количество новостей, которое вы получаете: <b>{user_quantity_news}</b>\n'

    if user_status == 1:
        message += '✔Активна ли ваша подписка (получаете ли вы регулярную рассылку погоды и новостей): <b>Да</b>'
    else:
        message += '✔Активна ли ваша подписка (получаете ли вы регулярную рассылку погоды и новостей): <b>Нет</b>'

    return message
