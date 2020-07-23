from datetime import datetime

import aiosqlite as lite

data = 'data/data.db'


async def add_new_user(user_id, user_name):
    """Добавление нового пользователя в базу, присваивание ему стандартных настроек"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT id FROM tbl_users WHERE id = ?", (user_id,))

        if not (user_id,) in await cur.fetchall():
            today = datetime.now()
            today = today.strftime("%d.%m.%Y")

            await cur.execute("INSERT INTO tbl_users(id, name, send_time, city, news_topics, quantity_news, status, "
                              "time_registered)"
                              "VALUES(?, ?, '08:00', 'Москва', 'Россия, бизнес, экономика, игры, образование', "
                              "'1', '1', ?)",
                              (user_id, str(user_name), str(today)))
            await con.commit()


async def change_user_parameter(user_id, section, info):
    """Смена определённого параметра пользвателя"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute(f"UPDATE tbl_users SET {section} = ? WHERE id = ?", (info, user_id,))
        await con.commit()


async def get_user_parameter(user_id, section):
    """Возвращает определённый параметр пользователя"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute(f"SELECT {section} FROM tbl_users WHERE id = ?", (user_id,))
        info = await cur.fetchall()
        return info[0][0]


async def get_all_user_parameters(user_id):
    """Возвращает все параметры пользователя"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT * FROM tbl_users WHERE id = ?", (user_id,))
        user_info = await cur.fetchall()
        return user_info[0]


async def get_all_user_info(user_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    user_info = await get_all_user_parameters(user_id)
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


async def get_all_users_info():
    """Возвращает информацию о всех пользователях"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT * FROM tbl_users")
        users_info = await cur.fetchall()
        return users_info


async def delete_user_info(user_id):
    """Удаляет пользователя из базы"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("DELETE FROM tbl_users WHERE id = ?", (user_id,))
        await con.commit()


async def add_new_group(group_id):
    """Добавление новой группы в БД, присваивание ей стандартных настроек"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT id FROM tbl_groups WHERE id = ?", (group_id,))

        if not (group_id,) in await cur.fetchall():
            today = datetime.now()
            today = today.strftime("%d.%m.%Y")

            await cur.execute("""INSERT INTO tbl_groups(id, send_hours, news_topics, quantity_news,
                                 status, time_added) 
                                 VALUES(?, '8, 12, 16, 20', 'Россия, бизнес, экономика, игры, образование', 
                                 '1', '1', ?)""", (group_id, str(today)))
            await con.commit()


async def change_group_parameter(group_id, section, info):
    """Смена определённого параметра группы"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute(f"UPDATE tbl_groups SET {section} = ? WHERE id = ?", (info, group_id,))
        await con.commit()


async def get_group_parameter(group_id, section):
    """Возвращает определённый параметр группы"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute(f"SELECT {section} FROM tbl_groups WHERE id = ?", (group_id,))
        info = await cur.fetchall()
        return info[0][0]


async def get_all_group_parameters(group_id):
    """Возвращает все параметры группы"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT * FROM tbl_groups WHERE id = ?", (group_id,))
        group_info = await cur.fetchall()
        return group_info[0]


async def get_all_groups_info():
    """Возвращает информацию о всех группах"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("SELECT * FROM tbl_groups")
        groups_info = await cur.fetchall()
        return groups_info


async def get_all_group_info(group_id):
    """Возвращает сообщение с информацией о настройках пользователя"""
    group_info = await get_all_group_parameters(group_id)
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


async def delete_group_info(group_id):
    """Удаляет группу из базы"""
    async with lite.connect(data) as con:
        cur = await con.cursor()
        await cur.execute("DELETE FROM tbl_groups WHERE id = ?", (group_id,))
        await con.commit()
