# Расположение исполнительных скриптов

## Скрипты импорта аудио (Analytics)

Скрипты для импорта аудио из внешних источников (АТС) должны быть размещены в этой папке (`scripts/`):

| Источник | Файл скрипта | Описание |
|----------|-------------|----------|
| ГазОйл | `import_from_ats_gazoil.py` | Импорт записей звонков из АТС ГазОйл |
| Евроойл | `import_from_ats_eurooil.py` | Импорт записей звонков из АТС Евроойл |
| КоллЦентр | `import_from_ats_callcentre.py` | Импорт записей звонков из АТС КоллЦентр |

### Ожидаемые аргументы скриптов импорта:

```bash
python import_from_ats_*.py \
    --date-from YYYY-MM-DD \
    --date-to YYYY-MM-DD \
    --phone "+7..." \
    --department "Название отдела" \
    --output /path/to/output/folder \
    --skip-existing \
    --min-duration 0
```

---

## Скрипты оценки звонков (Evaluation)

Скрипты для оценки транскрипций и формирования отчётов должны быть размещены в этой папке (`scripts/`):

| Источник | Файл скрипта | Описание |
|----------|-------------|----------|
| ГазОйл | `final_report_gazoil.py` | Оценка звонков и отчёт для ГазОйл |
| Евроойл | `final_report_eurooil.py` | Оценка звонков и отчёт для Евроойл |
| КоллЦентр | `final_report_callcentre.py` | Оценка звонков и отчёт для КоллЦентр |

### Ожидаемые аргументы скриптов оценки:

```bash
# Полный цикл (транскрибация + оценка)
python final_report_*.py

# Только сборка Excel из готовых оценок
python final_report_*.py --rebuild-excel

# Только оценка транскрипций
python final_report_*.py --eval-only
```

---

## Скрипт транскрибации

| Файл | Описание |
|------|----------|
| `1.py` | Основной скрипт транскрибации аудио |

### Ожидаемые аргументы скрипта транскрибации:

```bash
python 1.py \
    <audio_path> \
    --model tiny|base|small|medium|large|large-v2|large-v3|large-v3-turbo \
    --diarize \
    --no-diarize \
    --method ecapa|spectral \
    --output <path> \
    --timeout <ms> \
    --gpu <id> \
    --metadata '{"key": "value"}'
```

**По умолчанию:**
- model: `large-v3-turbo`
- diarize: `True` (включено)
- method: `spectral`
- timeout: `60000` мс
- gpu: `0`

---

## Примечания

1. Все скрипты должны быть исполняемыми и иметь корректный shebang (`#!/usr/bin/env python3`)
2. Скрипты запускаются от имени пользователя, под которым работает Django
3. Выходной код: `0` — успех, `1` — ошибка, `130` — прервано пользователем
4. Логи скриптов следует писать в stdout/stderr — они будут захвачены Django
