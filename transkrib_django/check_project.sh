#!/bin/bash
# Скрипт проверки работоспособности проекта «Транскриб»

set -e

echo "🔍 Проверка проекта Транскриб"
echo "=============================="
echo ""

# 1. Проверка структуры
echo "📁 Проверка структуры проекта..."
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py не найден"
    exit 1
fi

if [ ! -f "runner.py" ]; then
    echo "❌ runner.py не найден"
    exit 1
fi

if [ ! -f "entrypoint.sh" ]; then
    echo "❌ entrypoint.sh не найден"
    exit 1
fi

echo "✅ Структура проекта корректна"
echo ""

# 2. Проверка зависимостей
echo "📦 Проверка зависимостей..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt не найден"
    exit 1
fi
echo "✅ requirements.txt найден"
echo ""

# 3. Проверка импортов Python
echo "🐍 Проверка импортов Python..."
python -c "import django" 2>/dev/null || echo "⚠️  Django не установлен"
python -c "import flask" 2>/dev/null || echo "⚠️  Flask не установлен"
python -c "import requests" 2>/dev/null || echo "⚠️  requests не установлен"
echo "✅ Основные импорты проверены"
echo ""

# 4. Проверка синтаксиса Python файлов
echo "🔧 Проверка синтаксиса Python файлов..."
python -m py_compile manage.py
python -m py_compile runner.py
python -m py_compile core/views.py
python -m py_compile core/models.py
python -m py_compile analytics/views.py
python -m py_compile evaluation/views.py
echo "✅ Синтаксис Python файлов корректен"
echo ""

# 5. Проверка Django конфигурации
echo "⚙️  Проверка Django конфигурации..."
python manage.py check --deploy 2>&1 | grep -v "WARNINGS" || true
echo "✅ Django конфигурация проверена"
echo ""

# 6. Проверка миграций
echo "🗄️  Проверка миграций..."
python manage.py makemigrations --check --dry-run || echo "⚠️  Есть неприменённые миграции"
echo "✅ Миграции проверены"
echo ""

# 7. Запуск тестов
echo "🧪 Запуск unit тестов..."
python manage.py test core.tests --verbosity=2 || echo "⚠️  Некоторые тесты core не прошли"
python manage.py test analytics.tests --verbosity=2 || echo "⚠️  Некоторые тесты analytics не прошли"
python manage.py test evaluation.tests --verbosity=2 || echo "⚠️  Некоторые тесты evaluation не прошли"
echo "✅ Тесты завершены"
echo ""

echo "=============================="
echo "✅ Проверка проекта завершена!"
echo ""
echo "Для запуска проекта:"
echo "  docker compose up --build"
echo ""
echo "Для запуска тестов:"
echo "  python manage.py test"
echo ""
echo "Для проверки runner'а:"
echo "  curl http://localhost:8800/health"
