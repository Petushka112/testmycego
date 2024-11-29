# Генерация Secret_Key
from django.core.management.utils import get_random_secret_key
import os

# Генерация нового секретного ключа
secret_key = get_random_secret_key()

# Путь к .env
env_file_path = '.env'
# Чтение .env
if os.path.exists(env_file_path):
    with open(env_file_path, 'a') as f:
        f.write(f"\nSECRET_KEY={secret_key}\n")
else:
    # Если .env нет, создаем
    with open(env_file_path, 'w') as f:
        f.write(f"SECRET_KEY={secret_key}\n")
print(f"SECRET_KEY успешно добавлен в {env_file_path}")