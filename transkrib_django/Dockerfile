# Транскриб · версия 2: Django + Flask-runner в одном контейнере
FROM python:3.11-slim

# ffmpeg нужен для определения длительности загруженных медиа (ffprobe).
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Предпроверка: ключевые модули должны импортироваться ещё на этапе сборки.
RUN python -c "import config.settings, core, runner" \
    || (echo "ОШИБКА: не хватает config/, core/ или runner.py — проверьте контекст сборки" && exit 1)

RUN chmod +x entrypoint.sh

EXPOSE 8000 8800

ENTRYPOINT ["./entrypoint.sh"]
