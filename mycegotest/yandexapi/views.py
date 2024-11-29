import os
import logging
import requests
from django.shortcuts import render, redirect
from django.http import HttpResponse
from zipfile import ZipFile
from django.core.cache import cache

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("yandexapi.log"),
        logging.StreamHandler()
    ]
)

# REST API Яндекс.Диск
YANDEX_DISK_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"

# Конфигурация кэша
CACHE_DIR = "yandexapi/cache/"
CACHE_TIMEOUT = 3600


# Получение данных по публичной ссылке
def get_files_list(public_key: str, path: str = "") -> dict:
    cache_key = f"files_list_{public_key}_{path}"
    cached_data = cache.get(cache_key)

    # Проверка на наличие кэша
    if cached_data:
        logging.info(f"Использование кэшированных данных для public_key={public_key}, path={path}")
        return cached_data

    # Если кэш отсутствует, запрашиваем
    params = {"public_key": public_key, "path": path}
    logging.info(f"Запрос списка файлов: public_key={public_key}, path={path}")
    response = requests.get(YANDEX_DISK_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    # Кэшируем результат
    cache.set(cache_key, data, CACHE_TIMEOUT)
    logging.info(f"Кэширование данных для public_key={public_key}, path={path}")
    return data


# Скачивание файла
def download_file(public_key: str, file_path: str) -> str:
    logging.info(f"Скачивание файла: {file_path} (public_key={public_key})")
    params = {"public_key": public_key, "path": file_path}
    response = requests.get(f"{YANDEX_DISK_API_URL}/download", params=params)
    response.raise_for_status()
    download_url = response.json().get("href")
    file_response = requests.get(download_url)
    filename = file_path.split("/")[-1]
    os.makedirs(CACHE_DIR, exist_ok=True)
    local_path = os.path.join(CACHE_DIR, filename)
    with open(local_path, "wb") as f:
        f.write(file_response.content)
    logging.info(f"Файл {filename} успешно загружен в кэш.")
    return local_path

# Интерфейс страницы
def index(request):
    public_key = request.GET.get("public_key", "")
    path = request.GET.get("path", "")
    file_type = request.GET.get("file_type", "all")
    if not public_key:
        logging.warning("Не указана публичная ссылка.")
        return render(request, "index.html", {"error": "Укажите публичную ссылку."})
    try:
        data = get_files_list(public_key, path)
        items = data.get("_embedded", {}).get("items", [])

        # Фильтрация по типу файлов
        if file_type != "all":
            logging.info(f"Фильтрация файлов по типу: {file_type}")
            items = [f for f in items if f.get("mime_type", "").startswith(file_type)]
        logging.info(f"Успешная загрузка содержимого директории: {path or 'корень'}")
        return render(
            request,
            "index.html",
            {
                "files": items,
                "public_key": public_key,
                "path": path,
                "parent_path": data.get("path", "").rpartition("/")[0],
                "file_type": file_type,
            },
        )
    except Exception as e:
        logging.error(f"Ошибка при загрузке содержимого: {e}")
        return render(request, "index.html", {"error": str(e)})


# Загрузка одного файла/нескольких файлов
def download_selected_files(request):
    if request.method == "POST":
        public_key = request.POST.get("public_key")
        file_paths = request.POST.getlist("file_paths")
        if not file_paths:
            logging.warning("Пользователь не выбрал файлы для скачивания.")
            return redirect("index")
        try:
            if len(file_paths) == 1:

                # Скачивание одного файла без архивации
                file_path = file_paths[0]
                local_file = download_file(public_key, file_path)
                filename = os.path.basename(local_file)
                logging.info(f"Скачивание одиночного файла: {filename}")
                with open(local_file, "rb") as f:
                    response = HttpResponse(
                        f.read(),
                        content_type="application/octet-stream"
                    )
                    response["Content-Disposition"] = f"attachment; filename={filename}"
                    return response

            # Скачивание нескольких файлов в архиве
            zip_filename = "downloads.zip"
            zip_path = os.path.join(CACHE_DIR, zip_filename)
            with ZipFile(zip_path, "w") as zipf:
                for file_path in file_paths:
                    local_file = download_file(public_key, file_path)
                    zipf.write(local_file, os.path.basename(local_file))
            logging.info(f"Скачивание {len(file_paths)} файлов в архиве: {zip_filename}")
            with open(zip_path, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/zip")
                response["Content-Disposition"] = f"attachment; filename={zip_filename}"
                return response
        except Exception as e:
            logging.error(f"Ошибка при скачивании файлов: {e}")
            return redirect("index")
