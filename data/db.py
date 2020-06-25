import sqlite3 as lite
from datetime import datetime

data_users = 'data\\data.db'


def add_new_user(user_id, user_name):
    """Добавление нового пользователя в базу, присваивание ему стандартных настроек"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("SELECT id FROM tbl_users WHERE id = ?", (user_id,))

    if not(user_id,) in cur.fetchall():
        con = lite.connect(data_users)
        cur = con.cursor()

        today = datetime.now()
        today = today.strftime("%d.%m.%Y")

        cur.execute("INSERT INTO tbl_users(id, name, send_time, city, news_topic, quantity_news, status, progress, "
                    "time_registered)"
                    "VALUES(?, ?, '08:00', 'Москва', 'Россия', '1', '1', 'started', ?)", (user_id, str(user_name),
                                                                                          str(today)))
        con.commit()

    cur.close()
    con.close()


def change_user_parameter(user_id, section, info):
    """Смена определённого параметра пользвателя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(f"UPDATE tbl_users SET {section} = ? WHERE id = ?", (info, user_id,))
    con.commit()
    cur.close()
    con.close()


def get_user_parameter(user_id, section):
    """Возвращает определённый параметр пользователя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(f"SELECT {section} FROM tbl_users WHERE id = ?", (user_id,))
    info = cur.fetchall()
    cur.close()
    con.close()
    return info[0][0]


def get_all_user_parameters(user_id):
    """Возвращает все параметры пользователя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users WHERE id = ?", (user_id,))
    user_info = cur.fetchall()
    cur.close()
    con.close()
    return user_info[0]


def get_all_users_info():
    """Возвращает информацию о всех пользователях"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users")
    users_info = cur.fetchall()
    cur.close()
    con.close()
    return users_info


def delete_user_info(user_id):
    """Удаляет пользователя из базы"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("DELETE FROM tbl_users WHERE user_id = ?", (user_id,))
    con.commit()
    cur.close()
    con.close()


def get_all_user_info(user_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    user_info = get_all_user_parameters(user_id)
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
