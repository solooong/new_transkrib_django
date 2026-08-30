#!/bin/sh
# Точка входа: готовит данные, поднимает Flask-runner, затем Django. Оба — в этом контейнере.
set -e

mkdir -p /app/data /app/logs /app/media/uploads /app/media/results /app/staticfiles

# Предпроверка: пакет config должен импортироваться ДО запуска Django
if ! python -c "import importlib,sys; sys.path.insert(0,'/app'); importlib.import_module('config.settings')"; then
  echo ""
  echo "=== ОШИБКА: не импортируется config.settings ==="
  echo "Содержимое /app:"
  ls -la /app
  echo ""
  echo "Проверьте, что рядом с manage.py есть папка config/ (с __init__.py, settings.py, urls.py),"
  echo "и что docker compose запускается из корня проекта: docker compose up --build"
  exit 1
fi

echo "[entrypoint] миграции..."
python manage.py makemigrations core --noinput
python manage.py migrate --noinput

echo "[entrypoint] статика..."
python manage.py collectstatic --noinput

echo "[entrypoint] демо-данные (ADMIN_USERNAME/ADMIN_PASSWORD, по умолчанию admin/admin)..."
python manage.py seed_demo

# --- Flask-runner (фоновый процесс) ----------------------------------------
echo "[entrypoint] запуск Flask-runner'а на :${RUNNER_PORT:-8800}..."
python runner.py &
RUNNER_PID=$!

# Ждём, пока runner ответит на /health (до ~10 секунд).
i=0
while [ "$i" -lt 20 ]; do
  if python - <<'PY'
import os, urllib.request, sys
port = os.environ.get("RUNNER_PORT", "8800")
try:
    urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  then
    echo "[entrypoint] runner готов"
    break
  fi
  i=$((i + 1))
  sleep 0.5
done

echo "[entrypoint] запуск Django на :8000"
exec python manage.py runserver 0.0.0.0:8000
