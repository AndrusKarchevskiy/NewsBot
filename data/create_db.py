import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE tbl_users
                  (id INTEGER, name TEXT, send_time TEXT, city TEXT, news_topic TEXT, 
                  quantity_news INTEGER, status INTEGER, progress TEXT, time_registered TEXT)
               """)
