# 📋 Инструкция по разрешению конфликтов слияния

## Проблема

GitHub сообщает о конфликтах в следующих файлах:
```
transkrib_django/analytics/views.py
transkrib_django/config/settings.py
transkrib_django/core/urls.py
transkrib_django/core/utils.py
transkrib_django/data/db.sqlite3          ← бинарный файл
transkrib_django/evaluation/views.py
transkrib_django/logs/django.log          ← бинарный файл
transkrib_django/requirements.txt
transkrib_django/runner.py
```

## ✅ Решение

Все файлы в рабочей директории **уже исправлены** и содержат правильные версии. 
Маркеры конфликтов Git отсутствуют. Нужно только удалить бинарные файлы из Git 
и закоммитить изменения.

## 🔧 Шаги для разрешения

### 1. Удалите бинарные файлы из Git

```bash
cd transkrib_django

# Удалить бинарные файлы из индекса Git (но оставить в файловой системе)
git rm --cached data/db.sqlite3
git rm --cached logs/django.log

# Создать пустые placeholder файлы (опционально)
mkdir -p data logs
touch data/.gitkeep logs/.gitkeep
```

### 2. Добавьте все исправления

```bash
# Добавить все изменения
git add .

# Или добавить конкретные файлы
git add analytics/views.py
git add config/settings.py
git add core/urls.py
git add core/utils.py
git add evaluation/views.py
git add requirements.txt
git add runner.py
git add .gitignore
```

### 3. Закоммитьте изменения

```bash
git commit -m "Fix merge conflicts and remove binary files

- Fix incorrect timezone imports in analytics/views.py and evaluation/views.py
- Update requirements.txt with all necessary dependencies
- Fix runner.py to use correct script arguments
- Update entrypoint.sh to run migrations for all apps
- Remove binary files (db.sqlite3, django.log) from Git
- Add .gitignore to prevent future binary file commits"
```

### 4. Отправьте изменения

```bash
git push origin <your-branch-name>
```

## 📝 Что было исправлено

### analytics/views.py
✅ Исправлен неправильный импорт:
```python
# Было: __import__('django.utils').utils.timezone.now()
# Стало: from django.utils import timezone; timezone.now()
```

### evaluation/views.py
✅ Исправлен неправильный импорт (аналогично analytics/views.py)

### requirements.txt
✅ Добавлены все необходимые зависимости:
- openai-whisper, torch, torchaudio (транскрибация)
- pyannote.audio, speechbrain (диаризация)
- pandas, openpyxl (обработка данных)
- python-dotenv (переменные окружения)

### runner.py
✅ Обновлена команда запуска скрипта согласно контракту:
```python
# Было: [sys.executable, script, "--input", inp, "--output", out]
# Стало: [sys.executable, script, inp, "--output", out, "--model", model, ...]
```

### config/settings.py
✅ Добавлены приложения analytics и evaluation в INSTALLED_APPS

### core/urls.py
✅ Все URL-маршруты корректны

### core/utils.py
✅ Добавлен параметр method в payload для runner'а

### data/db.sqlite3 и logs/django.log
✅ Удалены из Git, добавлены в .gitignore

## 🎯 Результат

После выполнения этих шагов:
- ✅ Все конфликты будут разрешены
- ✅ Бинарные файлы больше не будут отслеживаться Git
- ✅ Все исправления будут закоммичены
- ✅ Pull request можно будет смержить

## 🧪 Проверка

После разрешения конфликтов проверьте работоспособность:

```bash
# Проверка структуры
cd transkrib_django
./check_project.sh

# Запуск тестов
python manage.py test

# Запуск проекта
docker compose up --build
```
