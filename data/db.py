import sqlite3 as lite
from datetime import datetime


data = 'data\\data.db'


def add_new_user(user_id, user_name):
    """Добавление нового пользователя в базу, присваивание ему стандартных настроек"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT id FROM tbl_users WHERE id = ?", (user_id,))

    if not (user_id,) in cur.fetchall():
        today = datetime.now()
        today = today.strftime("%d.%m.%Y")

        cur.execute("INSERT INTO tbl_users(id, name, send_time, city, news_topics, quantity_news, status, "
                    "time_registered)"
                    "VALUES(?, ?, '08:00', 'Москва', 'Россия, бизнес, экономика, игры, спорт, образование', "
                    "'1', '1', ?)",
                    (user_id, str(user_name), str(today)))
        con.commit()

    cur.close()
    con.close()


def change_user_parameter(user_id, section, info):
    """Смена определённого параметра пользвателя"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute(f"UPDATE tbl_users SET {section} = ? WHERE id = ?", (info, user_id,))
    con.commit()
    cur.close()
    con.close()


def get_user_parameter(user_id, section):
    """Возвращает определённый параметр пользователя"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute(f"SELECT {section} FROM tbl_users WHERE id = ?", (user_id,))
    info = cur.fetchall()
    cur.close()
    con.close()
    return info[0][0]


def get_all_user_parameters(user_id):
    """Возвращает все параметры пользователя"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users WHERE id = ?", (user_id,))
    user_info = cur.fetchall()
    cur.close()
    con.close()
    return user_info[0]


def get_all_user_info(user_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    user_info = get_all_user_parameters(user_id)
    user_send_time = user_info[2]
    user_city = user_info[3]
    user_news_topic = user_info[4]
    user_quantity_news = user_info[5]
    user_status = user_info[6]

    message = f'✔Время, в которое ты получаешь новости и погоду: <b>{user_send_time}</b>\n' \
              f'✔Город, из которого ты получаешь сводку погоды: <b>{user_city}</b>\n' \
              f'✔Ключевое слово (фраза), по которой ты получаешь новости: <b>{user_news_topic}</b>\n' \
              f'✔Количество новостей, которое ты получаешь: <b>{user_quantity_news}</b>\n'

    if user_status == 1:
        message += '✔Активна ли твоя подписка на рыссылку погоды и новостей? -- <b>Активна</b>'
    else:
        message += '✔Активна ли твоя подписка на рыссылку погоды и новостей? -- <b>Не активна</b>'

    return message


def get_all_users_info():
    """Возвращает информацию о всех пользователях"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users")
    users_info = cur.fetchall()
    cur.close()
    con.close()
    return users_info


def delete_user_info(user_id):
    """Удаляет пользователя из базы"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("DELETE FROM tbl_users WHERE id = ?", (user_id,))
    con.commit()
    cur.close()
    con.close()


def add_new_group(group_id):
    """Добавление новой группы в БД, присваивание ей стандартных настроек"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT id FROM tbl_groups WHERE id = ?", (group_id,))

    if not (group_id,) in cur.fetchall():
        today = datetime.now()
        today = today.strftime("%d.%m.%Y")

        cur.execute("""INSERT INTO tbl_groups(id, send_hours, news_topics, quantity_news,
                    status, time_added) 
                    VALUES(?, '8, 12, 16, 20', 'Россия, Америка, спорт, авто, игры, бизнес', 
                    '1', '1', ?)""", (group_id, str(today)))

        con.commit()
        
    cur.close()
    con.close()


def change_group_parameter(group_id, section, info):
    """Смена определённого параметра группы"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute(f"UPDATE tbl_groups SET {section} = ? WHERE id = ?", (info, group_id,))
    con.commit()
    cur.close()
    con.close()


def get_group_parameter(group_id, section):
    """Возвращает определённый параметр группы"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute(f"SELECT {section} FROM tbl_groups WHERE id = ?", (group_id,))
    info = cur.fetchall()
    cur.close()
    con.close()
    return info[0][0]


def get_all_group_parameters(group_id):
    """Возвращает все параметры группы"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_groups WHERE id = ?", (group_id,))
    group_info = cur.fetchall()
    cur.close()
    con.close()
    return group_info[0]


def get_all_groups_info():
    """Возвращает информацию о всех группах"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_groups")
    groups_info = cur.fetchall()
    cur.close()
    con.close()
    return groups_info


def get_all_group_info(group_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    group_info = get_all_group_parameters(group_id)
    group_news_topics = group_info[1]
    group_send_hours = group_info[2]
    group_quantity_news = group_info[3]
    group_status = group_info[4]

    message = f'✔Часы, в которые группа получает новости: <b>{group_send_hours}</b>\n' \
              f'✔Темы новостей, по которым группа получает новости: <b>{group_news_topics}</b>\n' \
              f'✔Количество новостей, которое за раз получает группа: <b>{group_quantity_news}</b>\n'

    if group_status == 1:
        message += '✔Активна ли подписка группы на рыссылку новостей? -- <b>Активна</b>'
    else:
        message += '✔Активна ли подписка группы на рыссылку новостей? -- <b>Не активна</b>'

    return message


def delete_group_info(group_id):
    """Удаляет группу из базы"""
    con = lite.connect(data)
    cur = con.cursor()
    cur.execute("DELETE FROM tbl_groups WHERE id = ?", (group_id,))
    con.commit()
    cur.close()
    con.close()
