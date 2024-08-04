import os
import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from monitor.server_monitor import monitor_server
from monitor.log_analyzer import analyze_logs, setup_logging
from monitor.command_handler import handle_command
from monitor.telegram_notifier import send_alert

# Настройка логирования
setup_logging()

async def start(update, context):
    """
    Обработчик команды /start
    """
    await update.message.reply_text('Бот запущен и готов к работе!')

async def main():
    """
    Основная асинхронная функция для запуска бота и выполнения задач
    """
    # Инициализация Telegram Application
    application = (
        Application.builder()
        .token(os.getenv('BOT_TOKEN'))
        .build()
    )

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_command))

    # Запуск бота
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    logging.info("Бот запущен и работает.")

    # Выполнение мониторинга сервера и анализа логов
    await monitor_server()
    analyze_logs()

    # Поддержка работы приложения до остановки
    await application.idle()

if __name__ == '__main__':
    asyncio.run(main())
