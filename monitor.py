import os
import sys
import subprocess
import requests
import telebot
import psutil
from dotenv import load_dotenv
from file_manager import FileManager  # Импортируем класс для работы с файлами


# Функция для установки зависимостей
def install_dependencies():
    try:
        # Обновление pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        # Установка зависимостей из файла requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)


# Установка зависимостей перед запуском основного кода
install_dependencies()

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена и ID чата из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Проверка, что BOT_TOKEN и CHAT_ID установлены
if not BOT_TOKEN or not CHAT_ID:
    print("Error: BOT_TOKEN and CHAT_ID must be set in the .env file.")
    sys.exit(1)

# Инициализация бота с использованием токена
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация FileManager для работы с файлами
file_manager = FileManager(bot, CHAT_ID)


# Проверка состояния сервера
def get_server_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    # Проверка интернет-соединения
    try:
        requests.get("http://www.google.com", timeout=5)
        internet_status = "Connected"
    except requests.ConnectionError:
        internet_status = "Disconnected"

    status_message = (
        f"Server Status:\n"
        f"CPU Usage: {cpu_usage}%\n"
        f"Memory Usage: {memory_usage}%\n"
        f"Disk Usage: {disk_usage}%\n"
        f"Internet Connection: {internet_status}"
    )

    return status_message


# Обновление пакетов
def update_packages():
    try:
        subprocess.run(['sudo', 'apt', 'update', '-y'], check=True)
        subprocess.run(['sudo', 'apt', 'upgrade', '-y'], check=True)
        bot.send_message(CHAT_ID, "Packages updated successfully.")
    except subprocess.CalledProcessError as e:
        bot.send_message(CHAT_ID, f"Error updating packages: {e}")


# Команды бота
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/help - помощь\n"
        "/update - обновить пакеты\n"
        "/status - проверить состояние сервера\n"
        "/edit <filename> - изменить содержимое файла\n"
        "Отправьте текст для добавления или удаления после команды /edit."
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['update'])
def update_cmd(message):
    bot.send_message(message.chat.id, "Updating packages...")
    update_packages()


@bot.message_handler(commands=['status'])
def status_cmd(message):
    status_message = get_server_status()
    bot.send_message(message.chat.id, status_message)


@bot.message_handler(commands=['edit'])
def edit_file_cmd(message):
    file_manager.edit_file(message)


# Основной цикл
def main():
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
