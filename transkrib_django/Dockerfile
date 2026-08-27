FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# ffmpeg нужен для ffprobe (длительность записей) и вашему скрипту 1.py,
# gcc — для сборки psutil.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs /app/media/uploads /app/media/results /app/staticfiles \
    && chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
