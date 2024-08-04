import os
import sys
import subprocess
import requests
import telebot
import psutil
import time
from dotenv import load_dotenv


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

# Переменная для хранения состояния терминального режима
terminal_mode = False


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
        # Автоматическое подтверждение изменений в ufw
        subprocess.run(['sudo', 'ufw', '--force', 'enable'], check=True)
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
    global terminal_mode
    terminal_mode = True
    bot.send_message(message.chat.id, "Terminal mode enabled.")


@bot.message_handler(commands=['termoff'])
def stop_terminal(message):
    global terminal_mode
    terminal_mode = False
    bot.send_message(message.chat.id, "Terminal mode disabled.")


@bot.message_handler(commands=['update'])
def update_cmd(message):
    bot.send_message(message.chat.id, "Updating packages...")
    update_packages()


@bot.message_handler(commands=['status'])
def status_cmd(message):
    status_message = get_server_status()
    bot.send_message(message.chat.id, status_message)


@bot.message_handler(commands=['vpn'])
def vpn_cmd(message):
    check_vpn_status()


@bot.message_handler(func=lambda message: True)
def handle_terminal_commands(message):
    global terminal_mode
    if terminal_mode:
        try:
            # Выполнение команды, отправленной в Telegram
            result = subprocess.run(message.text, shell=True, capture_output=True, text=True)
            if result.stdout:
                bot.send_message(message.chat.id, f"Output:\n{result.stdout}")
            if result.stderr:
                bot.send_message(message.chat.id, f"Error:\n{result.stderr}")
        except Exception as e:
            bot.send_message(message.chat.id, f"Failed to execute command: {e}")


# Основной цикл
def main():
    setup_firewall()
    bot.polling(none_stop=True)


if __name__ == '__main__':
    main()
