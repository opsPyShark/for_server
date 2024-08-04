import logging
from monitor.server_monitor import monitor_server

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )

    # Запуск мониторинга сервера
    monitor_server()
