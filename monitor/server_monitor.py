import requests
import logging
from monitor.telegram_notifier import send_alert

# Инициализация логирования
logger = logging.getLogger(__name__)

async def monitor_server():
    """
    Асинхронно мониторит состояние сервера и отправляет уведомления при обнаружении проблем.
    """
    try:
        # Пример проверки доступности сервера
        response = requests.get('http://example.com/health-check', timeout=5)

        # Проверка кода состояния
        if response.status_code != 200:
            message = f'Сервер вернул недопустимый код состояния: {response.status_code}'
            logger.error(message)
            await send_alert(message)
        else:
            # Отправляем уведомление о запуске и нормальной работе
            message = f'Бот запущен. Состояние сервера: {response.status_code}'
            logger.info(message)
            await send_alert(message)

        # Дополнительные проверки (например, на наличие ключевых слов в ответе)
        if 'error' in response.text.lower():
            message = 'Обнаружена ошибка в ответе сервера!'
            logger.error(message)
            await send_alert(message)

    except requests.exceptions.Timeout:
        message = 'Превышено время ожидания ответа от сервера!'
        logger.error(message)
        await send_alert(message)
    except requests.exceptions.RequestException as e:
        message = f'Ошибка при проверке сервера: {e}'
        logger.error(message)
        await send_alert(message)
