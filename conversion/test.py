from dotenv import load_dotenv
import os

# Загрузите переменные окружения из файла .env
load_dotenv()

# Получите переменную окружения
db_password = os.getenv('DB_PASSWORD')

print(f"Database password: {db_password}")