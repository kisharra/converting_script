from custom_logging.logger import CustomLogger

custom_logger = CustomLogger(log_dir="logs", max_files=30, rotation_interval=30)
logger = custom_logger.get_logger()

class Test:
    def __init__(self):
        pass

    def test(self):
        logger.info("Тестирование логгера начато.")
        logger.error("Это тестовая ошибка.")

if __name__ == "__main__":
    test = Test()
    test.test()
