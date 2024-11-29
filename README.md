Взаимодействие с API Яндекс.Диск
Запуск веб-приложения

1. Клонирование с git

git clone https://github.com/Petushka112/testmycego.git

3. Создание виртуального окружения если нет
   
python3 -m venv venv  -Unix/Linux/macOS

py -m venv venv  -Windows
	
5. Установка зависимостей
   
cd testmycego

pip install -r requirements.txt

7. Генерация secret_key
   
cd testmycego/mycegotest

python generate.py

9. Запуск локального сервера с приложением
    
cd testmycego/mycegotest

python manage.py runserver
   
