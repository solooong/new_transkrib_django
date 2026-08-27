#!/bin/sh
# Точка входа контейнера: подготовка данных, миграции, демо-данные, запуск.
set -e

mkdir -p /app/data /app/logs /app/media/uploads /app/media/results /app/staticfiles

echo "[entrypoint] миграции..."
python manage.py makemigrations core --noinput
python manage.py migrate --noinput

echo "[entrypoint] статика..."
python manage.py collectstatic --noinput

echo "[entrypoint] демо-данные (admin/admin)..."
python manage.py seed_demo

echo "[entrypoint] запуск сервера на :8000"
exec python manage.py runserver 0.0.0.0:8000
