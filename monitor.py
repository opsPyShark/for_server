import os
import subprocess
import sys
import asyncio
import psutil
import requests
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

def install_requirements():
    """Проверка и установка зависимостей из файла requirements.txt."""
    # Проверяем, установлен ли pip3
    try:
        import pip
    except ImportError:
        print("pip не установлен. Установка pip...")
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--default-pip"])

    # Проверка и установка зависимостей
    try:
        print("Проверка и установка зависимостей из requirements.txt...")
        with open("requirements.txt", "r") as file:
            required_packages = file.read().splitlines()

        # Установим отсутствующие пакеты
        installed_packages = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        installed_packages = installed_packages.decode().splitlines()
        installed_packages = {pkg.split('==')[0] for pkg in installed_packages}

        packages_to_install = [pkg for pkg in required_packages if pkg.split('==')[0] not in installed_packages]

        if packages_to_install:
            print(f"Установка отсутствующих пакетов: {packages_to_install}")
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages_to_install)
        else:
            print("Все зависимости уже установлены.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при установке зависимостей: {e}")
        sys.exit(1)

# Установить зависимости перед импортом модулей
install_requirements()

# Загрузка переменных окружения из файла .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_telegram_message(bot: Bot, message, important=False):
    """Отправка сообщения в Telegram."""
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        if important:
            print(f"Важное сообщение отправлено: {message}")
        else:
            print(f"Сообщение отправлено: {message}")
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def check_cpu_usage(threshold=80):
    """Проверка загрузки процессора."""
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage, cpu_usage > threshold

def check_memory_usage(threshold=80):
    """Проверка использования памяти."""
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    return memory_usage, memory_usage > threshold

def check_disk_usage(threshold=80):
    """Проверка использования диска."""
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    return disk_usage, disk_usage > threshold

def check_network_latency(url="https://www.google.com"):
    """Проверка сетевой задержки (пинга)."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.elapsed.total_seconds(), False
        else:
            return None, True
    except requests.ConnectionError:
        return None, True

async def monitor_system(bot):
    """Мониторинг состояния системы."""
    cpu_usage, cpu_alert = check_cpu_usage()
    memory_usage, memory_alert = check_memory_usage()
    disk_usage, disk_alert = check_disk_usage()
    network_latency, network_alert = check_network_latency()

    alerts = []
    if cpu_alert:
        alerts.append(f"Предупреждение: высокая загрузка процессора - {cpu_usage}%")
    if memory_alert:
        alerts.append(f"Предупреждение: высокое использование памяти - {memory_usage}%")
    if disk_alert:
        alerts.append(f"Предупреждение: высокое использование диска - {disk_usage}%")
    if network_alert:
        alerts.append("Ошибка сети: невозможно подключиться к интернету")

    if alerts:
        for alert in alerts:
            await send_telegram_message(bot, alert, important=True)

    # Отправка общего отчета в Telegram
    report = (
        f"Отчет о состоянии сервера:\n"
        f"Загрузка процессора: {cpu_usage}%\n"
        f"Использование памяти: {memory_usage}%\n"
        f"Использование диска: {disk_usage}%\n"
        f"Задержка сети: {network_latency} секунд\n"
    )
    await send_telegram_message(bot, report)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка справки."""
    help_text = (
        "/help - Показать это сообщение\n"
        "Мониторинг системы автоматически выполняется в фоновом режиме."
    )
    await update.message.reply_text(help_text)

async def start_monitoring():
    """Основная функция для инициализации и запуска бота."""
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("help", help_command))

    # Получение бота для отправки сообщений
    bot = Bot(token=TELEGRAM_TOKEN)

    # Запуск циклического мониторинга каждые 5 минут
    async def periodic_monitoring():
        while True:
            await monitor_system(bot)
            await asyncio.sleep(300)  # 5 минут

    # Запуск бота и мониторинга параллельно
    await asyncio.gather(application.start(), periodic_monitoring())

if __name__ == "__main__":
    print("Мониторинг сервера запущен.")
    asyncio.run(start_monitoring())
