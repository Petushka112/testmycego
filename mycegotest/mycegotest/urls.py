from django.urls import path
from yandexapi import views # Импортируем функционал приложения

urlpatterns = [
    path("", views.index, name="index"),
    path("download/", views.download_selected_files, name="download_selected_files"),
]
