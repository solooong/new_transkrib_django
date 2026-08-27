"""Запуск внешнего скрипта транскрибации (scripts/1.py) с потоковым логом.

Скрипт 1.py проектом НЕ изменяется: он подключается volume-ом и вызывается
по контракту (см. scripts/README.md). Если интерфейс аргументов другой —
задайте TRANSCRIBE_CMD в окружении, например:

    TRANSCRIBE_CMD="python scripts/1.py {input} {output}"
"""
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import threading

from django.conf import settings
from django.db import connections
from django.utils import timezone

logger = logging.getLogger("core.tasks")

_sem_lock = threading.Lock()
_semaphore: threading.BoundedSemaphore | None = None

RE_ERR = re.compile(r"error|traceback|exception|failed|не удалось|ошибка", re.I)
RE_WARN = re.compile(r"warn|skip|пропуск|предупрежд", re.I)
RE_OK = re.compile(r"\bdone\b|готово|завершено|успешно|\bok\b|success", re.I)
RE_PROGRESS = re.compile(r"(\d{1,3})\s*%")


def _sem() -> threading.BoundedSemaphore:
    """Семафор ограничения одновременных задач (ленивая инициализация)."""
    global _semaphore
    with _sem_lock:
        if _semaphore is None:
            _semaphore = threading.BoundedSemaphore(
                max(1, getattr(settings, "MAX_CONCURRENT_TASKS", 1))
            )
        return _semaphore


def add_log(task, text: str, level: str = "info") -> None:
    from .models import TaskLog

    TaskLog.objects.create(task=task, level=level, text=text)


def classify_level(line: str) -> str:
    if RE_ERR.search(line):
        return "err"
    if RE_WARN.search(line):
        return "warn"
    if RE_OK.search(line):
        return "ok"
    return "info"


def extract_progress(line: str):
    """Последнее вхождение 'NN%' в строке, если есть."""
    matches = RE_PROGRESS.findall(line)
    if not matches:
        return None
    value = int(matches[-1])
    return max(0, min(100, value))


def build_command(task) -> list[str]:
    """Команда запуска внешнего скрипта для задачи."""
    inp = task.input_file.path
    out = task.result_folder()
    
    # Сохраняем output_path в задаче
    if task.output_path:
        out = task.output_path
        os.makedirs(out, exist_ok=True)
    
    template = getattr(settings, "TRANSCRIBE_CMD", "")
    if template:
        return [part.format(input=inp, output=out) for part in shlex.split(template)]
    
    # Строим команду с аргументами согласно спецификации
    cmd = [sys.executable, settings.TRANSCRIBE_SCRIPT_PATH]
    cmd.extend(["--input", inp])
    cmd.extend(["--output", out])
    cmd.extend(["--model", task.model])
    
    if task.diarization:
        cmd.append("--diarize")
        cmd.extend(["--method", task.diarization_method])
    else:
        cmd.append("--no-diarize")
    
    cmd.extend(["--timeout", str(task.timeout_sec)])
    cmd.extend(["--gpu", str(task.gpu_id)])
    
    if task.metadata_json:
        cmd.extend(["--metadata", task.metadata_json])
    
    return cmd


def get_duration_sec(path: str):
    """Длительность медиа через ffprobe; None, если определить не удалось."""
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float(json.loads(proc.stdout)["format"]["duration"])
    except Exception:
        return None


def run_transcription(task_id: int) -> None:
    """Выполняет транскрибацию: стримит вывод скрипта в TaskLog, следит за прогрессом."""
    from .models import Task

    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return

    task.status = Task.Status.RUNNING
    task.error = ""
    task.save(update_fields=["status", "error", "updated_at"])

    cmd = build_command(task)
    add_log(task, "$ " + " ".join(shlex.quote(c) for c in cmd), "info")

    script_path = settings.TRANSCRIBE_SCRIPT_PATH
    if not getattr(settings, "TRANSCRIBE_CMD", "") and not os.path.isfile(script_path):
        msg = (
            f"Скрипт не найден: {script_path} "
            f"(каталог TRANSCRIBE_SCRIPT_DIR='{settings.TRANSCRIBE_SCRIPT_DIR}', "
            f"файл TRANSCRIBE_SCRIPT_NAME='{settings.TRANSCRIBE_SCRIPT_NAME}'). "
            f"Положите файл '{settings.TRANSCRIBE_SCRIPT_NAME}' в каталог "
            f"'{settings.TRANSCRIBE_SCRIPT_DIR}/' (см. scripts/README.md) "
            f"или задайте TRANSCRIBE_CMD."
        )
        add_log(task, msg, "err")
        task.status = Task.Status.ERROR
        task.error = msg
        task.save(update_fields=["status", "error", "updated_at"])
        return

    os.makedirs(task.result_folder(), exist_ok=True)

    try:
        logger.info("task %s: starting %s", task_id, cmd)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=settings.BASE_DIR,
        )
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.rstrip()
            if not line:
                continue
            add_log(task, line, classify_level(line))
            progress = extract_progress(line)
            if progress is not None and progress != task.progress:
                task.progress = progress
                task.save(update_fields=["progress", "updated_at"])

        code = proc.wait()
        task.refresh_from_db()

        if code == 0:
            files = task.result_files()
            add_log(task, f"[done] процесс завершён с кодом 0 · файлов в результатах: {len(files)}", "ok")
            task.status = Task.Status.DONE
            task.progress = 100
            task.finished_at = timezone.now()
            task.save(update_fields=["status", "progress", "finished_at", "updated_at"])
            logger.info("task %s: done", task_id)
        else:
            msg = f"Процесс завершился с кодом {code}"
            add_log(task, f"[exit] {msg}", "err")
            task.status = Task.Status.ERROR
            task.error = msg
            task.save(update_fields=["status", "error", "updated_at"])
            logger.warning("task %s: %s", task_id, msg)
    except Exception as exc:
        add_log(task, f"[fatal] {exc}", "err")
        task.status = Task.Status.ERROR
        task.error = str(exc)
        task.save(update_fields=["status", "error", "updated_at"])
        logger.exception("task %s crashed", task_id)
    finally:
        connections.close_all()


def start_transcription(task_id: int) -> None:
    """Запускает задачу в фоновом потоке с ограничением параллелизма."""

    def _worker() -> None:
        with _sem():
            run_transcription(task_id)

    thread = threading.Thread(target=_worker, name=f"task-{task_id}", daemon=True)
    thread.start()
