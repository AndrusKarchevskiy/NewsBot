import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))
OWM_TOKEN = str(os.getenv("OWM_TOKEN"))
NEWS_TOKEN = str(os.getenv("NEWS_TOKEN")).split(', ')
CARD_NUMBER = str(os.getenv("CARD_NUMBER"))
MY_NAME = str(os.getenv("MY_NAME"))
