import os
import logging
from datetime import datetime

class CustomLogger:
    def __init__(self, log_dir="logs", max_files=30, rotation_interval=30):
        self.log_dir = log_dir
        self.max_files = max_files
        self.rotation_interval = rotation_interval
        self.current_log_file = None
        self.last_rotation_time = None
        self.logger = None

        # Создание директории для логов, если она не существует
        os.makedirs(self.log_dir, exist_ok=True)

        self._rotate_log_file()
        self._setup_logger()

    def _rotate_log_file(self):
        """Создает новый файл лога и настраивает обработчик файла."""
        now = datetime.now()

        if self.last_rotation_time and self.last_rotation_time.date() == now.date():
            return  # Интервал ротации ещё не истёк

        self.last_rotation_time = now

        # Формат имени файла: YYYY-MM-DD.log
        log_file_name = now.strftime("%Y-%m-%d" + ".log")
        self.current_log_file = os.path.join(self.log_dir, log_file_name)

        with open(self.current_log_file, "a"):
            pass

        # Очищаем старые логи после создания нового файла
        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """Удаляет старые файлы логов, если их количество превышает max_files."""
        log_files = [
            os.path.join(self.log_dir, f)
            for f in os.listdir(self.log_dir)
            if f.endswith(".log")
        ]
        log_files.sort(key=os.path.getmtime)  # Сортировка по времени изменения

        while len(log_files) > self.max_files:
            oldest_file = log_files.pop(0)
            os.remove(oldest_file)

    def get_log_file(self):
        """Возвращает текущий файл лога."""
        self._rotate_log_file()
        return self.current_log_file

    def _setup_logger(self):
        """Настраивает логгер и добавляет кастомный обработчик."""
        self.logger = logging.getLogger("CustomLogger")

        # Удаляем существующие обработчики, чтобы избежать дублирования
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        self.logger.setLevel(logging.DEBUG)

        log_handler = LoggingHandler(self)
        log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(log_handler)

    def get_logger(self):
        """Возвращает настроенный логгер."""
        self._rotate_log_file()
        self._setup_logger()
        return self.logger

class LoggingHandler(logging.Handler):
    def __init__(self, custom_logger):
        super().__init__()
        self.custom_logger = custom_logger

    def emit(self, record):
        """Записывает сообщение в текущий лог-файл."""
        log_entry = self.format(record)
        log_file = self.custom_logger.get_log_file()
        with open(log_file, "a") as file:
            file.write(log_entry + "\n")

# if __name__ == "__main__":
#     custom_logger = CustomLogger(log_dir="logs", max_files=30, rotation_interval=30)
#     logger = custom_logger.get_logger()
#     logger.info("Тестирование логгера начато.")
#     logger.error("Это тестовая ошибка.")