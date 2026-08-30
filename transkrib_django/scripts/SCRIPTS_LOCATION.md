# 📁 Расположение скриптов проекта «Транскриб»

Все исполняемые скрипты должны находиться в папке **`/workspace/transkrib_django/scripts/`**.

Эта папка подключена к Docker-контейнеру как volume, поэтому вы можете редактировать скрипты на хосте без пересборки образа.

---

## 🔹 Скрипты импорта аудио (Аналитика звонков)

| Файл | Назначение | Аргументы CLI |
|------|-----------|---------------|
| `import_from_ats_gazoil.py` | Импорт записей из системы ГазОйл | `--date-from`, `--date-to`, `--phone`, `--department`, `--output`, `--skip-existing`, `--min-duration` |
| `import_from_ats_eurooil.py` | Импорт записей из системы Евроойл | `--date-from`, `--date-to`, `--phone`, `--department`, `--output`, `--skip-existing`, `--min-duration` |
| `import_from_ats_callcentre.py` | Импорт записей из системы КоллЦентр | `--date-from`, `--date-to`, `--phone`, `--department`, `--output`, `--skip-existing`, `--min-duration` |

### Пример запуска:
```bash
python scripts/import_from_ats_gazoil.py \
  --date-from 2024-01-01 \
  --date-to 2024-01-31 \
  --phone +79991234567 \
  --output /app/data/output/gazoil \
  --skip-existing \
  --min-duration 10
```

### Логика main (шаблон):
```python
def main() -> int:
    """Точка входа CLI приложения."""
    print("\n📞 Megafon Cloud PBX Downloader v3.0.0\n")
    
    # 1. Загрузка переменных окружения
    load_dotenv()
    api_token = os.getenv("MEGAFON_API_TOKEN")
    if not api_token:
        logger.error("❌ Required env var MEGAFON_API_TOKEN not found in .env")
        return 1
    
    # 2. Инициализация компонентов
    try:
        api_client = MegafonPBXClient(token=api_token)
        config_loader = ConfigLoader()
        db_manager = CallDbManager() 
        downloader = RecordingDownloader(api_client, config_loader, db_manager)        
    except Exception as exc:
        logger.exception(f"❌ Initialization failed: {exc}")
        return 1
    
    # 3. Получение диапазона дат от пользователя
    try:
        start = prompt_for_date("📅 Start date")
        end = prompt_for_date("📅 End date")
        
        if start > end:
            print("❌ Error: Start date must be before end date")
            return 1
    except KeyboardInterrupt:
        print("\n⚠️  Cancelled by user")
        return 130
    
    # 4. Запуск выгрузки
    try:
        stats = downloader.run(start, end)
        summary = stats.to_summary()
        # ... вывод статистики
        return 0 if summary['failed'] == 0 else 1
    except Exception as exc:
        logger.exception("💥 Critical runtime error")
        return 1
    finally:
        if 'db_manager' in locals():
            db_manager.close()


if __name__ == "__main__":
    sys.exit(main())
```

---

## 🔹 Скрипты оценки звонков

| Файл | Назначение | Аргументы CLI |
|------|-----------|---------------|
| `final_report_gazoil.py` | Оценка транскрипций для ГазОйл | `--rebuild-excel`, `--eval-only` |
| `final_report_eurooil.py` | Оценка транскрипций для Евроойл | `--rebuild-excel`, `--eval-only` |
| `final_report_callcentre.py` | Оценка транскрипций для КоллЦентр | `--rebuild-excel`, `--eval-only` |

### Пример запуска:
```bash
# Только сборка Excel из готовых оценок
python scripts/final_report_gazoil.py --rebuild-excel

# Только оценка транскрипций
python scripts/final_report_gazoil.py --eval-only

# Полный процесс (транскрибация + оценка)
python scripts/final_report_gazoil.py
```

### Логика main (шаблон):
```python
if __name__ == "__main__":
    if not check_dependencies():
        exit(1)
    
    db_manager = CallDbManager()
    try:  # ← ДОБАВИТЬ ЭТУ СТРОКУ
        if "--rebuild-excel" in sys.argv:
            # Только сборка Excel из готовых оценок
            output_folder = OUT_PUT_FOLDER
            rebuild_excel_from_evaluations(output_folder)
            exit(0)  # ← ОБЯЗАТЕЛЬНО, иначе идёт дальше

        if "--eval-only" in sys.argv:
            # Только оценка транскрипций
            output_folder = OUT_PUT_FOLDER
            excel_report = os.path.join(output_folder, "transcription_report.xlsx")
            print("🚀 Запуск ТОЛЬКО оценки транскрипций...")
            evaluate_transcriptions(output_folder, excel_report, db_manager)
            exit(0)
        
        # ... остальной код основного запуска
        print("=== Система транскрибации и оценки аудио ===")
        
        # Получаем пути
        input_folder = RECORDS_FOLDER.strip().strip('"')
        output_folder = OUT_PUT_FOLDER.strip().strip('"')
        
        # Проверяем пути
        if not os.path.exists(input_folder):
            print("❌ Ошибка: папка с аудиофайлами не существует")
            exit(1)
        
        # Создаем папку для результатов
        os.makedirs(output_folder, exist_ok=True)
        
        # Транскрибация
        processed_files, failed_files = transcribe_audio(input_folder, output_folder)
        
        if processed_files:
            # Оценка и создание отчета
            excel_report = os.path.join(output_folder, "transcription_report.xlsx")
            evaluation_results = evaluate_transcriptions(output_folder, excel_report, db_manager)
            
            # Сохраняем финальный прогресс
            save_progress_tracker(input_folder, output_folder, processed_files, failed_files)
            
            # Общая статистика
            print("\n🎉 ПРОЦЕСС ЗАВЕРШЕН!")
            print(f"📊 Обработано файлов: {len(processed_files)}")
            
    finally:  # ← ДОБАВИТЬ ЭТИ ДВЕ СТРОКИ
        db_manager.close()  # ← ОБЯЗАТЕЛЬНО закрываем соединение
```

---

## 🔹 Скрипт транскрибации

| Файл | Назначение |
|------|-----------|
| `1.py` | Основной скрипт транскрибации аудио |

### Аргументы CLI:
```bash
python scripts/1.py \
  <audio_path> \
  --model <tiny|base|small|medium|large|large-v2|large-v3|large-v3-turbo> \
  [--diarize] [--no-diarize] \
  [--method ecapa|spectral] \
  [--output <path>] \
  [--timeout <ms>] \
  [--gpu <id>] \
  [--metadata <json>]
```

### Подробное описание аргументов:
| Аргумент | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `audio_path` | positional | — | Путь к аудиофайлу (WAV, MP3, M4A, AMR и др.) |
| `--model` | choice | `large-v3-turbo` | Размер модели Whisper |
| `--diarize` | flag | `True` | Разделение по спикерам (включено по умолчанию) |
| `--no-diarize` | flag | `False` | Отключить разделение по спикерам |
| `--method` | choice | `spectral` | Метод диаризации (ecapa или spectral) |
| `--output` | str | — | Путь для сохранения результата |
| `--timeout` | int | `60000` | Таймаут транскрибации в миллисекундах |
| `--gpu` | int | `0` | ID GPU для использования |
| `--metadata` | str | — | JSON строка с метаданными |

### Пример запуска:
```bash
python scripts/1.py \
  /app/data/records/call_123.wav \
  --model large-v3-turbo \
  --diarize \
  --method spectral \
  --output /app/data/output/transcription_123.json \
  --timeout 60000 \
  --gpu 0 \
  --metadata '{"call_id": "123", "agent": "Ivanov"}'
```

---

## 📂 Структура папки scripts/

```
/workspace/transkrib_django/scripts/
├── 1.py                              # Скрипт транскрибации
├── import_from_ats_gazoil.py         # Импорт из ГазОйл
├── import_from_ats_eurooil.py        # Импорт из Евроойл
├── import_from_ats_callcentre.py     # Импорт из КоллЦентр
├── final_report_gazoil.py            # Оценка ГазОйл
├── final_report_eurooil.py           # Оценка Евроойл
├── final_report_callcentre.py        # Оценка КоллЦентр
└── SCRIPTS_LOCATION.md               # Этот файл
```

---

## 🔧 Интеграция с Django

Django автоматически находит и запускает эти скрипты через `subprocess.Popen`:

1. **Аналитика звонков** (`/analytics/`):
   - Выбираете источник (ГазОйл/Евроойл/КоллЦентр)
   - Указываете даты, фильтры, путь вывода
   - Django запускает соответствующий `import_from_ats_*.py`

2. **Оценка звонков** (`/evaluation/`):
   - Выбираете источник (ГазОйл/Евроойл/КоллЦентр)
   - Опции: только Excel, только оценка, полный процесс
   - Django запускает соответствующий `final_report_*.py`

3. **Загрузка файла** (`/upload/`):
   - Загружаете аудиофайл через форму
   - Указываете параметры транскрибации
   - Django запускает `scripts/1.py` с указанными аргументами

---

## ⚙️ Переменные окружения

Некоторые скрипты используют переменные окружения из `.env`:

```bash
# МегаФон API
MEGAFON_API_TOKEN=your_token_here

# Пути к данным
RECORDS_FOLDER=/app/data/records
OUT_PUT_FOLDER=/app/data/output

# Настройки транскрибации по умолчанию
DEFAULT_WHISPER_MODEL=large-v3-turbo
DEFAULT_DIARIZE=1
DEFAULT_DIARIZATION_METHOD=spectral
DEFAULT_TIMEOUT_MS=60000
DEFAULT_GPU_ID=0
```

---

## 🧪 Тестирование

После добавления скриптов проверьте их работу:

```bash
# Проверка синтаксиса
python -m py_compile scripts/1.py
python -m py_compile scripts/import_from_ats_gazoil.py
python -m py_compile scripts/final_report_gazoil.py

# Запуск с --help (если реализовано)
python scripts/1.py --help
python scripts/import_from_ats_gazoil.py --help
python scripts/final_report_gazoil.py --help
```

---

## 📝 Примечания

1. Все скрипты должны быть исполняемыми и иметь корректный shebang: `#!/usr/bin/env python3`
2. Скрипты должны возвращать код выхода: `0` — успех, `1` — ошибка, `130` — прервано
3. Обязательно закрывайте соединения с БД в блоке `finally`
4. Логируйте все ошибки через `logger.exception()`
5. Поддерживайте интерактивный режим (опрос пользователя) и CLI-режим (аргументы)
