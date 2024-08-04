import subprocess
import sys


def install_requirements():
    """Установка зависимостей из файла requirements.txt."""
    # Проверяем, установлен ли pip3
    try:
        import pip
    except ImportError:
        print("pip не установлен. Установка pip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])

    # Установка зависимостей из requirements.txt
    try:
        print("Установка зависимостей из requirements.txt...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Зависимости установлены успешно.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        sys.exit(1)


# Установить зависимости перед импортом модулей
install_requirements()

# Теперь можно импортировать необходимые модули
import os
import psutil
import requests
from dotenv import load_dotenv
from telegram import Bot

# Загрузка переменных окружения из файла .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Инициализация бота
bot = Bot(token=TELEGRAM_TOKEN)


def send_telegram_message(message, important=False):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        if important:
            print(f"Важное сообщение отправлено: {message}")
        else:
            print(f"Сообщение отправлено: {message}")
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")


def check_cpu_usage(threshold=80):
    """Проверка загрузки процессора."""
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > threshold:
        message = f"Предупреждение: высокая загрузка процессора - {cpu_usage}%"
        send_telegram_message(message, important=True)
    return cpu_usage


def check_memory_usage(threshold=80):
    """Проверка использования памяти."""
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    if memory_usage > threshold:
        message = f"Предупреждение: высокое использование памяти - {memory_usage}%"
        send_telegram_message(message, important=True)
    return memory_usage


def check_disk_usage(threshold=80):
    """Проверка использования диска."""
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    if disk_usage > threshold:
        message = f"Предупреждение: высокое использование диска - {disk_usage}%"
        send_telegram_message(message, important=True)
    return disk_usage


def check_network_latency(url="https://www.google.com"):
    """Проверка сетевой задержки (пинга)."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            message = f"Сайт {url} доступен. Задержка: {response.elapsed.total_seconds()} секунд"
        else:
            message = f"Ошибка доступа к сайту {url}. Статус: {response.status_code}"
            send_telegram_message(message, important=True)
    except requests.ConnectionError:
        message = f"Ошибка сети: невозможно подключиться к {url}"
        send_telegram_message(message, important=True)


def main():
    # Отправка уведомления о запуске мониторинга
    send_telegram_message("Мониторинг сервера запущен", important=True)

    print("Проверка состояния сервера и сети...")
    cpu_usage = check_cpu_usage()
    memory_usage = check_memory_usage()
    disk_usage = check_disk_usage()
    check_network_latency()

    # Отправка общего отчета в Telegram
    report = (
        f"Отчет о состоянии сервера:\n"
        f"Загрузка процессора: {cpu_usage}%\n"
        f"Использование памяти: {memory_usage}%\n"
        f"Использование диска: {disk_usage}%\n"
    )
    send_telegram_message(report)


if __name__ == "__main__":
    main()
