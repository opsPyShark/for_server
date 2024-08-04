import os
import logging
import asyncio
import subprocess
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /help
    """
    help_text = (
        "Доступные команды:\n"
        "/help - Показать эту справку\n"
        "/monitor - Проверить состояние сервера\n"
        "/server_reboot - Перезагрузить сервер\n"
        "/vpn_restart - Перезапустить VPN\n"
    )
    await update.message.reply_text(help_text)

async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /monitor для проверки состояния сервера
    """
    try:
        # Пример проверки доступности сервера
        response = subprocess.run(["curl", "-Is", "http://example.com"], capture_output=True, text=True)
        if "200 OK" in response.stdout:
            await update.message.reply_text("Сервер работает нормально.")
        else:
            await update.message.reply_text("Сервер вернул ошибку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при проверке сервера: {e}")

async def server_reboot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /server_reboot для перезагрузки сервера
    """
    if str(update.effective_user.id) == CHAT_ID:
        try:
            await update.message.reply_text("Сервер будет перезагружен.")
            subprocess.run(["sudo", "reboot"], check=True)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при перезагрузке сервера: {e}")
    else:
        await update.message.reply_text("У вас нет разрешения на выполнение этой команды.")

async def vpn_restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /vpn_restart для перезапуска VPN
    """
    if str(update.effective_user.id) == CHAT_ID:
        try:
            # Путь к скрипту reset.sh
            script_path = "/root/auto_opnvpn/reset.sh"
            subprocess.run(["sudo", "bash", script_path], check=True)
            await update.message.reply_text("VPN был перезапущен.")
        except Exception as e:
            await update.message.reply_text(f"Ошибка при перезапуске VPN: {e}")
    else:
        await update.message.reply_text("У вас нет разрешения на выполнение этой команды.")

async def main():
    """
    Основная асинхронная функция для запуска бота
    """
    # Инициализация Telegram Application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("monitor", monitor_command))
    application.add_handler(CommandHandler("server_reboot", server_reboot_command))
    application.add_handler(CommandHandler("vpn_restart", vpn_restart_command))

    # Запуск бота
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    logging.info("Бот запущен и работает.")

    # Поддержка работы приложения до остановки
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
