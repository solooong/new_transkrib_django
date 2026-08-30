"""Взаимодействие Django с Flask-runner'ом.

Архитектура v2: Django больше не запускает скрипт напрямую. Она передаёт задачу
по HTTP в Flask-runner (тот же контейнер, см. runner.py), который запускает
внешний скрипт транскрибации и шлёт результаты обратно через callback-API
(/api/runner/log|progress|done|error).
"""
import json
import logging
import os
import subprocess
import threading
import time

import requests
from django.conf import settings
from django.db import connections

logger = logging.getLogger("core.tasks")


def add_log(task, text: str, level: str = "info") -> None:
    from .models import TaskLog

    TaskLog.objects.create(task=task, level=level, text=text)


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


def runner_health() -> bool:
    """Жив ли Flask-runner (быстрый опрос /health)."""
    try:
        resp = requests.get(settings.RUNNER_URL.rstrip("/") + "/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def _build_payload(task) -> dict:
    """Пакет данных для runner-а: что запускать и куда слать результат."""
    return {
        "task_id": task.pk,
        "script": settings.TRANSCRIBE_SCRIPT_PATH,
        "input": task.input_file.path,
        "output_dir": task.result_folder(),
        "language": task.language,
        "model": task.model,
        "diarization": task.diarization,
        "callback_base": settings.DJANGO_INTERNAL_BASE,
        "secret": settings.RUNNER_SECRET,
    }


def _dispatch(task_id: int) -> None:
    """Фоновая отправка задачи в runner с ретраями."""
    from .models import Task

    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return

    task.status = Task.Status.RUNNING
    task.progress = 0
    task.error = ""
    task.save(update_fields=["status", "progress", "error", "updated_at"])

    script = settings.TRANSCRIBE_SCRIPT_PATH
    add_log(task, f"[runner] передача задачи в обработку · скрипт {os.path.basename(script)}", "info")

    payload = _build_payload(task)
    url = settings.RUNNER_URL.rstrip("/") + "/run"

    for attempt in range(1, 4):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code in (200, 202):
                add_log(task, "[runner] задача принята в работу", "ok")
                logger.info("task %s dispatched to runner", task_id)
                return
            logger.warning("runner answered %s for task %s", resp.status_code, task_id)
        except Exception as exc:
            logger.warning("dispatch attempt %s for task %s failed: %s", attempt, task_id, exc)
        time.sleep(1.2 * attempt)

    # Не удалось связаться с runner-ом.
    msg = (
        "Runner недоступен: не удалось передать задачу в обработку. "
        f"Проверьте, что runner запущен ({settings.RUNNER_URL}/health), и нажмите «Повторить»."
    )
    add_log(task, f"[runner] {msg}", "err")
    task.status = Task.Status.ERROR
    task.error = msg
    task.save(update_fields=["status", "error", "updated_at"])
    connections.close_all()


def dispatch_to_runner(task_id: int) -> None:
    """Запускает отправку задачи в runner в фоновом потоке."""
    threading.Thread(target=_dispatch, args=(task_id,), name=f"dispatch-{task_id}", daemon=True).start()
