import logging
from monitor.server_monitor import monitor_server
from monitor.log_analyzer import analyze_logs, setup_logging

if __name__ == "__main__":
    setup_logging()

    logging.info("Запуск мониторинга сервера.")

    # Запуск мониторинга сервера
    monitor_server()

    # Анализ логов после мониторинга
    analyze_logs()
