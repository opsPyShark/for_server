import logging
import os
from monitor.telegram_notifier import send_alert

LOG_FILE = 'server_monitor.log'

def analyze_logs():
    """
    Анализирует логи и отправляет уведомления о найденных ошибках.
    """
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, 'r') as file:
        logs = file.readlines()

    errors = [log for log in logs if 'ERROR' in log]

    if errors:
        message = "Обнаружены ошибки в логах:\n" + "".join(errors[-5:])  # Отправляем последние 5 ошибок
        send_alert(message)

def setup_logging():
    """
    Настраивает логирование в файл.
    """
    logging.basicConfig(
        filename=LOG_FILE,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
