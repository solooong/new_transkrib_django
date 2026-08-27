FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# ffmpeg/ffprobe — для определения длительности загруженных записей
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Страховка: каталоги, которые монтируются volume-ами, должны существовать
RUN mkdir -p /app/scripts /app/data /app/logs /app/media/uploads /app/media/results /app/staticfiles \
    && chmod +x /app/entrypoint.sh

# Предпроверка структуры до запуска: если config/ не попал в образ —
# сразу понятная ошибка со списком файлов, а не ModuleNotFoundError.
RUN ls /app/config/settings.py >/dev/null \
    && ls /app/core/models.py >/dev/null \
    && ls /app/manage.py >/dev/null \
    || (echo "=== ОШИБКА СБОРКИ: в образе нет config/ или core/ ===" && exit 1)

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
