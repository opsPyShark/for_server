import os
import psutil
import subprocess
import docker
from scapy.all import sniff, IP
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
from threading import Thread
import logging
import asyncio

# Загрузка токена из .env файла
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # Убедитесь, что CHAT_ID также есть в .env

# Проверка токена
if not TOKEN:
    raise ValueError("Telegram token is missing! Please set it in the .env file.")

# Создание клиента Docker
client = docker.from_env()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для мониторинга
network_issues_detected = False


# Функции бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Я ваш серверный бот. Напишите /help для получения списка команд.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '/help - Список команд\n'
        '/reboot - Перезагрузить сервер\n'
        '/newvpn - Создать новое VPN-соединение\n'
        '/status - Статус сервера'
    )


async def reboot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Перезагрузка сервера...')
    subprocess.run(['sudo', 'reboot'])


async def new_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Остановка текущего VPN
        containers = client.containers.list(all=True, filters={"ancestor": "xtrime/antizapret-vpn-docker"})
        for container in containers:
            container.stop()
            container.remove()

        # Запуск нового VPN
        client.containers.run("xtrime/antizapret-vpn-docker", detach=True)
        await update.message.reply_text('Новое VPN-соединение установлено.')
    except Exception as e:
        await update.message.reply_text(f'Ошибка при создании VPN: {e}')


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    status_message = (
        f"Загрузка ЦП: {cpu_usage}%\n"
        f"Использование памяти: {memory.percent}%\n"
        f"Свободное место на диске: {disk.percent}%"
    )

    await update.message.reply_text(status_message)


def monitor_network():
    global network_issues_detected

    def packet_callback(packet):
        if IP in packet:
            ip_layer = packet[IP]
            # Пример анализа: если TTL меньше 10, считаем подозрительным
            if ip_layer.ttl < 10:
                logger.warning(f"Обнаружен подозрительный пакет: {ip_layer.src} -> {ip_layer.dst}")
                network_issues_detected = True

    # Запуск сниффера на фоне
    sniff(filter="ip", prn=packet_callback, store=0)


async def send_alerts(app):
    global network_issues_detected

    while True:
        if network_issues_detected:
            alert_message = "Обнаружены проблемы в сети!"
            await app.bot.send_message(chat_id=CHAT_ID, text=alert_message)
            # Сброс флага после отправки уведомления
            network_issues_detected = False
        await asyncio.sleep(10)  # Задержка между проверками


async def send_startup_message(app, message):
    # Отправка сообщения в Telegram о запуске
    await app.bot.send_message(chat_id=CHAT_ID, text=message)


def configure_firewall():
    try:
        subprocess.run(['sudo', 'ufw', 'enable'], check=True)
        subprocess.run(['sudo', 'ufw', 'allow', '22'], check=True)  # SSH доступ
        subprocess.run(['sudo', 'ufw', 'allow', '1194'], check=True)  # OpenVPN порт
        subprocess.run(['sudo', 'ufw', 'default', 'deny', 'incoming'], check=True)  # Запрет входящих по умолчанию
        subprocess.run(['sudo', 'ufw', 'default', 'allow', 'outgoing'], check=True)  # Разрешение исходящих по умолчанию
        logger.info("Брандмауэр настроен.")
        return "Брандмауэр настроен."
    except subprocess.CalledProcessError as e:
        logger.error(f'Ошибка настройки брандмауэра: {e}')
        return f'Ошибка настройки брандмауэра: {e}'


def configure_shadowsocks():
    try:
        subprocess.run(['sudo', 'systemctl', 'enable', 'shadowsocks-libev'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', 'shadowsocks-libev'], check=True)
        logger.info("Shadowsocks запущен и настроен.")
        return "Shadowsocks запущен и настроен."
    except subprocess.CalledProcessError as e:
        logger.error(f'Ошибка настройки Shadowsocks: {e}')
        return f'Ошибка настройки Shadowsocks: {e}'


def configure_openvpn():
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'openvpn'], check=True)
        logger.info("OpenVPN перезапущен с новой конфигурацией.")

        # Запуск скрипта restart.sh после перезапуска OpenVPN
        subprocess.run(['/root/auto_opnvpn/restart.sh'], check=True)
        logger.info("Скрипт restart.sh выполнен.")

        return "OpenVPN перезапущен с новой конфигурацией и скрипт restart.sh выполнен."
    except subprocess.CalledProcessError as e:
        logger.error(f'Ошибка настройки OpenVPN: {e}')
        return f'Ошибка настройки OpenVPN: {e}'


def update_system():
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'], check=True)
        logger.info("Система обновлена.")
        return "Система обновлена."
    except subprocess.CalledProcessError as e:
        logger.error(f'Ошибка обновления системы: {e}')
        return f'Ошибка обновления системы: {e}'


def setup_fail2ban():
    try:
        subprocess.run(['sudo', 'systemctl', 'enable', 'fail2ban'], check=True)
        subprocess.run(['sudo', 'systemctl', 'start', 'fail2ban'], check=True)
        logger.info("Fail2ban запущен и настроен.")
        return "Fail2ban запущен и настроен."
    except subprocess.CalledProcessError as e:
        logger.error(f'Ошибка настройки Fail2ban: {e}')
        return f'Ошибка настройки Fail2ban: {e}'


async def main():
    # Создание и запуск приложения
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reboot", reboot))
    app.add_handler(CommandHandler("newvpn", new_vpn))
    app.add_handler(CommandHandler("status", status))

    # Настройка и запуск служб
    startup_messages = [
        configure_firewall(),
        configure_shadowsocks(),
        configure_openvpn(),
        update_system(),
        setup_fail2ban()
    ]

    # Отправка сообщений о запуске
    startup_message = "\n".join(startup_messages)
    await send_startup_message(app, f"Сервер запущен:\n{startup_message}")

    # Запуск мониторинга сети в отдельном потоке
    monitor_thread = Thread(target=monitor_network)
    monitor_thread.daemon = True
    monitor_thread.start()

    # Запуск отправки оповещений в отдельном потоке
    asyncio.create_task(send_alerts(app))

    await app.run_polling()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.error(f'Ошибка в главной функции: {e}')
