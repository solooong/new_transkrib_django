#!/bin/sh
# Точка входа контейнера: проверка структуры, миграции, демо-данные, запуск.
set -e

mkdir -p /app/data /app/logs /app/media/uploads /app/media/results /app/staticfiles

# Предпроверка: пакет config должен импортироваться ДО запуска Django
if ! python -c "import importlib,sys; sys.path.insert(0,'/app'); importlib.import_module('config.settings')"; then
  echo ""
  echo "=== ОШИБКА: не импортируется config.settings ==="
  echo "Содержимое /app:"
  ls -la /app
  echo ""
  echo "Проверьте, что в контексте сборки рядом с manage.py есть папка config/"
  echo "с файлами __init__.py, settings.py, urls.py, wsgi.py, asgi.py,"
  echo "и что docker compose запускается из корня проекта (docker compose up --build)."
  exit 1
fi

echo "[entrypoint] миграции..."
python manage.py makemigrations core --noinput
python manage.py migrate --noinput

echo "[entrypoint] статика..."
python manage.py collectstatic --noinput

echo "[entrypoint] демо-данные (пользователь из ADMIN_USERNAME/ADMIN_PASSWORD, по умолчанию admin/admin)..."
python manage.py seed_demo

echo "[entrypoint] запуск сервера на :8000"
exec python manage.py runserver 0.0.0.0:8000
