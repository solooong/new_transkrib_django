# new_transkrib_django

Веб-интерфейс для транскрибации речи: загрузка аудио, запуск внешнего скрипта
распознавания (`scripts/1.py`), живые логи, результаты и дашборд мониторинга
системы. Работает локально в Docker.

## Структура репозитория

```
.
├── transkrib_django/      ← основной Django-проект (запускается в Docker)
│   ├── config/            ← настройки, корневые URL, WSGI/ASGI
│   ├── core/              ← приложение: модели, воркер, метрики, вьюхи, шаблоны, JS
│   ├── scripts/           ← каталог скрипта транскрибации (TRANSCRIBE_SCRIPT_DIR)
│   ├── manage.py
│   ├── Dockerfile / docker-compose.yml / entrypoint.sh
│   └── requirements.txt
└── src/                   ← React-прототип дизайна дашборда (для референса)
```

## Быстрый старт

```bash
cd transkrib_django

# 1. Настройте окружение (опционально — всё работает и со значениями по умолчанию)
cp .env.example .env

# 2. Положите ваш скрипт распознавания как scripts/1.py
cp /путь/к/вашему/скрипту.py scripts/1.py

# 3. Соберите и запустите
docker compose up --build

# 4. Откройте http://localhost:8000 (порт меняется переменной TRANSCRIB_PORT в .env)
#    Вход: admin / admin (или из ADMIN_USERNAME / ADMIN_PASSWORD в .env)
```

## Куда класть скрипт транскрибации

Каталог задаётся переменной **`TRANSCRIBE_SCRIPT_DIR`** (по умолчанию `scripts`),
имя файла — **`TRANSCRIBE_SCRIPT_NAME`** (по умолчанию `1.py`). Скрипт
подключается volume-ом и проектом **не изменяется**. Подробнее —
[transkrib_django/scripts/README.md](transkrib_django/scripts/README.md).

## Проверка мониторинга системы

```bash
docker compose exec web python manage.py metrics_check
```

Выведет разовый замер CPU/RAM/GPU/диска/сети и сохранит точку в историю —
дашборд подхватит её автоматически.

## Полезное

- Админка Django: `http://localhost:8000/admin/`
- Демо-данные (задачи + история метрик) создаются командой `seed_demo` на старте.
- Логи: `transkrib_django/logs/django.log`.
- Полная документация — [transkrib_django/README.md](transkrib_django/README.md).
