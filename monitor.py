import os
import sys
import subprocess

# Функция для установки зависимостей
def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])  # Обновление pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

# Установка зависимостей перед запуском основного кода
install_dependencies()

import telebot
import psutil
import time
from dotenv import load_dotenv

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

# Проверка состояния сервера
def check_server_status():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent

    # Отправка сообщения, если нагрузка слишком высокая
    if cpu_usage > 80 or memory_usage > 80 or disk_usage > 90:
        bot.send_message(
            CHAT_ID,
            f"Warning: High resource usage detected!\nCPU: {cpu_usage}%\nMemory: {memory_usage}%\nDisk: {disk_usage}%"
        )

# Обновление пакетов
def update_packages():
    try:
        subprocess.run(['sudo', 'apt', 'update'], check=True)
        subprocess.run(['sudo', 'apt', 'upgrade', '-y'], check=True)
        bot.send_message(CHAT_ID, "Packages updated successfully.")
    except subprocess.CalledProcessError as e:
        bot.send_message(CHAT_ID, f"Error updating packages: {e}")

# Проверка состояния VPN
def check_vpn_status():
    try:
        result = subprocess.run(['docker', 'ps'], stdout=subprocess.PIPE)
        if 'antizapret-vpn-docker' not in result.stdout.decode():
            bot.send_message(CHAT_ID, "VPN is not running!")
            start_vpn()
    except Exception as e:
        bot.send_message(CHAT_ID, f"Error checking VPN status: {e}")

def start_vpn():
    try:
        subprocess.run(['docker', 'start', 'antizapret-vpn-docker'], check=True)
        bot.send_message(CHAT_ID, "VPN started successfully.")
    except subprocess.CalledProcessError as e:
        bot.send_message(CHAT_ID, f"Error starting VPN: {e}")

# Настройка защиты от атак (например, с использованием ufw)
def setup_firewall():
    try:
        subprocess.run(['sudo', 'ufw', 'enable'], check=True)
        subprocess.run(['sudo', 'ufw', 'allow', '22'], check=True)  # SSH
        subprocess.run(['sudo', 'ufw', 'allow', '1194/udp'], check=True)  # OpenVPN
        subprocess.run(['sudo', 'ufw', 'default', 'deny'], check=True)
        bot.send_message(CHAT_ID, "Firewall configured successfully.")
    except subprocess.CalledProcessError as e:
        bot.send_message(CHAT_ID, f"Error configuring firewall: {e}")

# Команды бота
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "/help - помощь\n"
        "/term - режим терминала\n"
        "/termoff - выключение режима терминала\n"
        "/update - обновить пакеты\n"
        "/status - проверить состояние сервера\n"
        "/vpn - проверить VPN\n"
    )
    bot.send_message(message.chat.id, help_text)

@bot.message_handler(commands=['term'])
def start_terminal(message):
    bot.send_message(message.chat.id, "Terminal mode enabled.")
    # Реализация терминального режима

@bot.message_handler(commands=['termoff'])
def stop_terminal(message):
    bot.send_message(message.chat.id, "Terminal mode disabled.")
    # Выключение терминального режима

@bot.message_handler(commands=['update'])
def update_cmd(message):
    bot.send_message(message.chat.id, "Updating packages...")
    update_packages()

@bot.message_handler(commands=['status'])
def status_cmd(message):
    check_server_status()
    bot.send_message(message.chat.id, "Server status checked.")

@bot.message_handler(commands=['vpn'])
def vpn_cmd(message):
    check_vpn_status()

# Основной цикл
def main():
    setup_firewall()
    bot.polling(none_stop=True)
    while True:
        check_server_status()
        check_vpn_status()
        update_packages()
        time.sleep(3600)  # Проверка каждый час

if __name__ == '__main__':
    main()
