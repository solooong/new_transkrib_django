"""
Настройки проекта «Транскриб» (версия 2).

Архитектура: Django (интерфейс и хранение) + Flask-runner (исполнение скрипта)
в одном контейнере. Мониторинг системы удалён — только транскрибация.
Все чувствительные параметры читаются из переменных окружения (.env).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, "1" if default else "0").lower() in ("1", "true", "yes", "on")


SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    "django-insecure-transkrib-local-dev-key-change-me-in-production",
)

DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "analytics",
    "evaluation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Авторизация -----------------------------------------------------------
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"

# --- Транскрибация ----------------------------------------------------------
# Каталог, в который кладётся файл скрипта транскрибации (по умолчанию scripts/).
# Подключается volume-ом ./scripts:/app/scripts — файл можно менять без пересборки.
TRANSCRIBE_SCRIPT_DIR = env("TRANSCRIBE_SCRIPT_DIR", "scripts")

# Имя файла скрипта внутри каталога TRANSCRIBE_SCRIPT_DIR.
TRANSCRIBE_SCRIPT_NAME = env("TRANSCRIBE_SCRIPT_NAME", "1.py")

# Полный путь к скрипту (передаётся runner-у).
TRANSCRIBE_SCRIPT_PATH = os.path.join(BASE_DIR, TRANSCRIBE_SCRIPT_DIR, TRANSCRIBE_SCRIPT_NAME)

# Сколько задач runner может выполнять одновременно.
MAX_CONCURRENT_TASKS = int(env("MAX_CONCURRENT_TASKS", "1"))

# --- Flask-runner -----------------------------------------------------------
# Адрес runner-а (тот же контейнер, запускается entrypoint'ом).
RUNNER_PORT = env("RUNNER_PORT", "8800")
RUNNER_URL = env("RUNNER_URL", f"http://127.0.0.1:{RUNNER_PORT}")

# Внутренний адрес Django, куда runner шлёт callback-и (лог/прогресс/результат).
DJANGO_INTERNAL_BASE = env("DJANGO_INTERNAL_BASE", "http://127.0.0.1:8000")

# Общий секрет для защиты callback-API (runner -> Django).
RUNNER_SECRET = env("RUNNER_SECRET", "dev-runner-secret-change-me")

# Максимальный размер загружаемого файла — 2 ГБ.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024 * 1024

# --- Логирование ------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "django.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "INFO"},
        "core": {"handlers": ["console", "file"], "level": "INFO"},
    },
}
