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

        cur.execute("INSERT INTO tbl_users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    (user_id, user_name, "08:00", "Москва", "Россия", "1", "1", "started", today))
        con.commit()


def change_user_parameter(user_id, section, info):
    """Смена определённого параметра пользвателя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(f"UPDATE tbl_users SET {section} = ? WHERE id = ?", (info, user_id,))
    con.commit()


def get_user_parameter(user_id, section):
    """Возвращает определённый параметр пользователя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(f"SELECT {section} FROM tbl_users WHERE id = ?", (user_id,))
    # Получаем список кортежей
    info = cur.fetchall()
    # Возвращаем параметр
    return info[0][0]


def get_all_user_parameters(user_id):
    """Возвращает все параметры пользователя"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users WHERE id = ?", (user_id,))
    user_info = cur.fetchall()
    return user_info[0]


def get_all_users_info():
    """Возвращает информацию о всех пользователях"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("SELECT * FROM tbl_users")
    users_info = cur.fetchall()
    print(users_info)
    return users_info


def delete_user_info(user_id):
    """Удаляет пользователя из базы"""
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("DELETE FROM tbl_users WHERE user_id = ?", (user_id,))
    con.commit()
