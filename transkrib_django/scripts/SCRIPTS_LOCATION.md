# 📁 Расположение исполнительных скриптов проекта

Этот документ описывает расположение и назначение всех исполнительных `.py` скриптов в проекте.

## Структура папки scripts/

Все скрипты должны быть размещены в папке `scripts/` рядом с этим файлом:

```
scripts/
├── 1.py                              # Скрипт транскрибации аудио
├── import_from_ats_gazoil.py         # Импорт аудио из АТС ГазОйл
├── import_from_ats_eurooil.py        # Импорт аудио из АТС Евроойл
├── import_from_ats_callcentre.py     # Импорт аудио из АТС КоллЦентр
├── final_report_gazoil.py            # Оценка звонков ГазОйл
├── final_report_eurooil.py           # Оценка звонков Евроойл
├── final_report_callcentre.py        # Оценка звонков КоллЦентр
└── SCRIPTS_LOCATION.md               # Этот файл
```

---

## 1. Скрипт транскрибации

### Файл: `scripts/1.py`

**Назначение:** Транскрибация аудиофайлов с использованием Whisper AI

**Аргументы командной строки:**

```bash
python scripts/1.py <audio_path> [OPTIONS]

Позиционные аргументы:
  audio_path              Путь к аудиофайлу (WAV, MP3, M4A, AMR и др.)

Опциональные аргументы:
  --model                 Размер модели Whisper
                          choices: tiny, base, small, medium, large, 
                                   large-v2, large-v3, large-v3-turbo
                          default: large-v3-turbo
  
  --diarize               Разделение по спикерам (по умолчанию включено)
  --no-diarize            Отключить разделение по спикерам
  
  --method                Метод диаризации
                          choices: ecapa, spectral
                          default: spectral
  
  --output                Путь для сохранения результата
  
  --timeout               Таймаут транскрибации в секундах
                          type: int
                          default: 60000
  
  --gpu                   ID GPU для использования
                          type: int
                          default: 1
  
  --metadata              JSON строка с метаданными
                          type: str
```

**Примеры использования:**

```bash
# Базовая транскрибация
python scripts/1.py /path/to/audio.wav

# С выбором модели и диаризацией
python scripts/1.py /path/to/audio.wav --model large-v3 --diarize --method ecapa

# С выводом в файл и таймаутом
python scripts/1.py /path/to/audio.wav --output /path/to/result.json --timeout 120000

# С использованием GPU и метаданными
python scripts/1.py /path/to/audio.wav --gpu 0 --metadata '{"call_id": "12345", "agent": "Ivanov"}'
```

**Возвращаемые значения:**
- `0` — успех
- `1` — ошибки
- `130` — прервано пользователем (Ctrl+C)

---

## 2. Скрипты импорта аудио (Аналитика звонков)

### Файл: `scripts/import_from_ats_gazoil.py`

**Назначение:** Загрузка записей звонков из АТС системы ГазОйл

**Раздел в интерфейсе:** Аналитика звонков → Импорт аудио ГазОйл

**Ожидаемые аргументы (рекомендуется):**
```bash
python scripts/import_from_ats_gazoil.py \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --phone +7XXXXXXXXXX \
    --output /path/to/output/folder
```

---

### Файл: `scripts/import_from_ats_eurooil.py`

**Назначение:** Загрузка записей звонков из АТС системы Евроойл

**Раздел в интерфейсе:** Аналитика звонков → Импорт аудио Евроойл

**Ожидаемые аргументы (рекомендуется):**
```bash
python scripts/import_from_ats_eurooil.py \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --phone +7XXXXXXXXXX \
    --output /path/to/output/folder
```

---

### Файл: `scripts/import_from_ats_callcentre.py`

**Назначение:** Загрузка записей звонков из АТС системы КоллЦентр

**Раздел в интерфейсе:** Аналитика звонков → Импорт аудио КоллЦентр

**Ожидаемые аргументы (рекомендуется):**
```bash
python scripts/import_from_ats_callcentre.py \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --phone +7XXXXXXXXXX \
    --output /path/to/output/folder
```

---

## 3. Скрипты оценки звонков

### Файл: `scripts/final_report_gazoil.py`

**Назначение:** Оценка качества звонков и формирование отчёта для ГазОйл

**Раздел в интерфейсе:** Оценка звонков → ГазОйл

**Аргументы командной строки:**
```bash
python scripts/final_report_gazoil.py [OPTIONS]

Опциональные аргументы:
  --rebuild-excel         Только сборка Excel из готовых оценок
  --eval-only             Только оценка транскрипций
```

**Логика работы:**

1. **Режим `--rebuild-excel`:**
   - Собирает Excel-отчёт из уже существующих оценок
   - Пропускает этап транскрибации
   - Выход после завершения (exit 0)

2. **Режим `--eval-only`:**
   - Выполняет только оценку транскрипций
   - Создаёт файл `transcription_report.xlsx`
   - Выход после завершения (exit 0)

3. **Полный режим (без флагов):**
   - Проверка зависимостей
   - Транскрибация аудиофайлов
   - Оценка транскрипций
   - Создание финального отчёта
   - Сохранение прогресса и статистики

**Примеры использования:**

```bash
# Только пересборка Excel
python scripts/final_report_gazoil.py --rebuild-excel

# Только оценка
python scripts/final_report_gazoil.py --eval-only

# Полный цикл
python scripts/final_report_gazoil.py
```

**Структура выходных данных:**
```
output_folder/
├── transcription_report.xlsx    # Финальный отчёт
├── processing_summary.json      # Статистика обработки
├── logs/                        # Логи выполнения
└── transcriptions/              # Расшифровки файлов
```

---

### Файл: `scripts/final_report_eurooil.py`

**Назначение:** Оценка качества звонков и формирование отчёта для Евроойл

**Раздел в интерфейсе:** Оценка звонков → Евроойл

**Аргументы и логика:** Аналогично `final_report_gazoil.py`

---

### Файл: `scripts/final_report_callcentre.py`

**Назначение:** Оценка качества звонков и формирование отчёта для КоллЦентр

**Раздел в интерфейсе:** Оценка звонков → КоллЦентр

**Аргументы и логика:** Аналогично `final_report_gazoil.py`

---

## Интеграция с Django

### Как Django запускает скрипты

Django вызывает скрипты через `subprocess.Popen()` с соответствующими аргументами:

```python
import subprocess

# Пример запуска скрипта импорта
cmd = [
    "python",
    "scripts/import_from_ats_gazoil.py",
    "--date-from", "2025-01-01",
    "--date-to", "2025-01-31",
    "--output", "/app/media/imports/gazoil/"
]
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
```

### Мониторинг выполнения

- Статус задания сохраняется в базе данных (модели `ImportJob`, `EvaluationJob`)
- Логи пишутся в реальном времени
- Пользователь видит прогресс через polling API

---

## Требования к скриптам

### Общие требования

1. **Возврат кодов выхода:**
   - `0` — успех
   - `1` — ошибка
   - `130` — прервано пользователем

2. **Логирование:**
   - Вывод в stdout/stderr
   - Поддержка цветного вывода (опционально)

3. **Обработка прерываний:**
   ```python
   try:
       # основная логика
   except KeyboardInterrupt:
       print("\n⚠️  Interrupted by user")
       exit(130)
   ```

4. **Зависимости:**
   - Все зависимости должны быть указаны в `requirements.txt`
   - Или установлены через `pip install`

### Для скриптов оценки (`final_report_*.py`)

Обязательная структура `main()`:

```python
def main() -> int:
    """Точка входа CLI приложения."""
    if not check_dependencies():
        return 1
    
    db_manager = CallDbManager()
    try:
        if "--rebuild-excel" in sys.argv:
            output_folder = OUT_PUT_FOLDER
            rebuild_excel_from_evaluations(output_folder)
            return 0
        
        if "--eval-only" in sys.argv:
            output_folder = OUT_PUT_FOLDER
            excel_report = os.path.join(output_folder, "transcription_report.xlsx")
            evaluate_transcriptions(output_folder, excel_report, db_manager)
            return 0
        
        # Основной код...
        return 0
    
    finally:
        db_manager.close()

if __name__ == "__main__":
    sys.exit(main())
```

---

## Переменные окружения

Некоторые скрипты могут требовать переменные окружения:

```bash
# Для скриптов импорта
MEGAFON_API_TOKEN=your_token_here

# Для скриптов оценки
RECORDS_FOLDER=/path/to/records
OUT_PUT_FOLDER=/path/to/output
```

Установите их в `.env` файле или `docker-compose.yml`.

---

## Тестирование скриптов

### Быстрый тест транскрибации

```bash
cd /workspace/transkrib_django

# Проверка наличия файла
ls -la scripts/1.py

# Тест с коротким аудио
python scripts/1.py tests/sample.wav --model tiny --timeout 30000
```

### Тест импорта

```bash
# Проверка синтаксиса
python -m py_compile scripts/import_from_ats_gazoil.py

# Запуск с help
python scripts/import_from_ats_gazoil.py --help
```

### Тест оценки

```bash
# Проверка синтаксиса
python -m py_compile scripts/final_report_gazoil.py

# Запуск с help
python scripts/final_report_gazoil.py --help
```

---

## Обновление скриптов

Если вы обновили скрипт:

1. Положите новую версию в `scripts/`
2. Перезапустите контейнер:
   ```bash
   docker compose restart web
   ```
3. Проверьте логи:
   ```bash
   docker compose logs -f web
   ```

---

## Контакты и поддержка

При возникновении проблем со скриптами:

1. Проверьте логи Django: `/workspace/transkrib_django/logs/`
2. Проверьте права доступа к файлам
3. Убедитесь, что все зависимости установлены
4. Проверьте переменные окружения
