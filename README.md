# new_transkrib_django

Веб-интерфейс для транскрибации речи (**версия 2**): загрузка аудио, запуск
внешнего скрипта распознавания (`scripts/1.py`) через **Flask-runner** в том же
контейнере, живые логи, сохранение и отображение транскрибаций пользователя,
скачивание результата в `.txt`. Работает локально в Docker. Мониторинг системы
удалён — только транскрибация.

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

## Как устроено (версия 2)

Django (`:8000`) отвечает за интерфейс, хранение и скачивание; **Flask-runner**
(`:8800`, тот же контейнер) запускает `scripts/1.py` и шлёт журнал, прогресс и
текст транскрипта обратно через callback-API. Индикатор «runner онлайн/офлайн» —
в шапке интерфейса.

Проверить runner вручную:

```bash
curl http://localhost:8800/health
```

Выведет разовый замер CPU/RAM/GPU/диска/сети и сохранит точку в историю —
дашборд подхватит её автоматически.

## Полезное

- Админка Django: `http://localhost:8000/admin/`
- Демо-данные (задачи + история метрик) создаются командой `seed_demo` на старте.
- Логи: `transkrib_django/logs/django.log`.
- Полная документация — [transkrib_django/README.md](transkrib_django/README.md).
