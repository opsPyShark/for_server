import os
from telegram import Bot
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

async def send_alert(message):
    """
    Асинхронно отправляет уведомление в Telegram.
    """
    if BOT_TOKEN and CHAT_ID:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    else:
        print("Ошибка: Не удалось отправить сообщение. Проверьте BOT_TOKEN и CHAT_ID в .env файле.")
