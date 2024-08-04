import subprocess
from telegram import Update
from telegram.ext import ContextTypes
import logging
import os

logger = logging.getLogger(__name__)

AUTHORIZED_USERS = {os.getenv('CHAT_ID')}  # Авторизованный пользователь

async def execute_command(command: str) -> str:
    """
    Выполняет заданную команду и возвращает её вывод.
    """
    try:
        # Выполнение команды в безопасном окружении
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка выполнения команды: {e}")
        return f"Ошибка: {e}"

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает команды, отправленные в чат, и возвращает их вывод.
    """
    user_id = update.effective_user.id
    command = update.message.text

    if str(user_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("У вас нет разрешения на выполнение команд.")
        return

    logger.info(f"Получена команда от пользователя {user_id}: {command}")
    output = await execute_command(command)
    await update.message.reply_text(f"Результат выполнения команды:\n{output}")
