import requests
from monitor.telegram_notifier import send_alert


def monitor_server():
    """
    Мониторит состояние сервера и отправляет уведомления при обнаружении проблем.
    """
    try:
        # Пример проверки доступности сервера
        response = requests.get('http://example.com/health-check', timeout=5)

        # Проверка кода состояния
        if response.status_code != 200:
            send_alert(f'Сервер вернул недопустимый код состояния: {response.status_code}')

        # Дополнительные проверки (например, на наличие ключевых слов в ответе)
        if 'error' in response.text.lower():
            send_alert('Обнаружена ошибка в ответе сервера!')

    except requests.exceptions.Timeout:
        send_alert('Превышено время ожидания ответа от сервера!')
    except requests.exceptions.RequestException as e:
        send_alert(f'Ошибка при проверке сервера: {e}')
