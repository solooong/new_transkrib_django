#!/usr/bin/env python
"""Flask-runner: исполняет скрипт транскрибации и отчитывается Django.

Работает в том же контейнере, что и Django (запускается entrypoint'ом).

Эндпоинты:
    GET  /health          — проверка доступности
    POST /run             — принять задачу и запустить скрипт в фоне

Получив задачу, runner запускает внешний скрипт (scripts/1.py — НЕ изменяется),
построчно пересылает его вывод в Django (callback /api/runner/log/), следит за
прогрессом (строки вида «NN%»), а в конце читает файл транскрипта из папки
результатов и отправляет его через /api/runner/done/.

Запуск вручную:  python runner.py   (порт — переменная RUNNER_PORT, по умолч. 8800)
"""
import os
import re
import subprocess
import sys
import threading

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

RUNNER_PORT = int(os.environ.get("RUNNER_PORT", "8800"))
RUNNER_SECRET = os.environ.get("RUNNER_SECRET", "dev-runner-secret-change-me")
MAX_CONCURRENT = max(1, int(os.environ.get("MAX_CONCURRENT_TASKS", "1")))

# Ограничение одновременных запусков скрипта (GPU/CPU).
_semaphore = threading.BoundedSemaphore(MAX_CONCURRENT)

RE_PROGRESS = re.compile(r"(\d{1,3})\s*%")


# --------------------------------------------------------------------------- helpers

def _classify(line: str) -> str:
    low = line.lower()
    if any(k in low for k in ("error", "traceback", "exception", "failed", "ошибка", "не удалось")):
        return "err"
    if any(k in low for k in ("warn", "skip", "пропуск", "предупрежд")):
        return "warn"
    if any(k in low for k in ("done", "готово", "завершено", "успешно", " ok", "success")):
        return "ok"
    return "info"


def _post(url: str, payload: dict, secret: str) -> None:
    """Callback в Django; ошибки не роняют runner."""
    try:
        requests.post(url, json=payload, headers={"X-Runner-Secret": secret}, timeout=10)
    except Exception as exc:  # pragma: no cover — сеть может моргнуть
        print(f"[runner] callback failed {url}: {exc}", file=sys.stderr, flush=True)


def _read_transcript(output_dir: str) -> str:
    """Читает транскрипт из папки результатов.

    Приоритет: transcript.txt / транскрипт.txt, иначе первый найденный .txt.
    """
    if not os.path.isdir(output_dir):
        return ""
    for name in ("transcript.txt", "транскрипт.txt"):
        path = os.path.join(output_dir, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read()
    for name in sorted(os.listdir(output_dir)):
        if name.lower().endswith(".txt"):
            with open(os.path.join(output_dir, name), encoding="utf-8", errors="replace") as f:
                return f.read()
    return ""


# --------------------------------------------------------------------------- исполнение

def _run(payload: dict) -> None:
    """Запуск скрипта транскрибации.
    
    Поддерживает динамический выбор скрипта через script_name.
    Если script_name указан, скрипт ищется в директории scripts/.
    """
    task_id = payload["task_id"]
    
    # Поддержка динамического выбора скрипта
    script_name = payload.get("script_name")  # Новое: имя скрипта из ProcessingScript
    script = payload.get("script")  # Старое: полный путь (для совместимости)
    
    # Если указан script_name, формируем полный путь
    if script_name:
        # script_name приходит как "scripts/1.py" или просто "1.py"
        if not script_name.startswith("scripts/"):
            script_name = f"scripts/{script_name}"
        # Формируем абсолютный путь
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(base_dir, script_name)
    
    inp = payload["input"]
    out = payload["output_dir"]
    cb = payload["callback_base"].rstrip("/")
    secret = payload["secret"]

    log_url = f"{cb}/api/runner/log/"
    prog_url = f"{cb}/api/runner/progress/"
    done_url = f"{cb}/api/runner/done/"
    err_url = f"{cb}/api/runner/error/"

    with _semaphore:
        os.makedirs(out, exist_ok=True)
        
        script_display = script_name if script_name else os.path.basename(script)
        _post(log_url, {"task_id": task_id, "level": "info",
                        "text": f"[runner] запуск: python {script_display} --input … --output …"}, secret)

        if not os.path.isfile(script):
            _post(log_url, {"task_id": task_id, "level": "err",
                            "text": f"[runner] скрипт не найден: {script} "
                                    f"(положите файл в каталог scripts/, см. README)"}, secret)
            _post(err_url, {"task_id": task_id, "error": f"Скрипт не найден: {script}"}, secret)
            return

        try:
            # Формируем команду согласно контракту скрипта 1.py
            cmd = [sys.executable, script, inp, "--output", out]
            
            # Добавляем опции из payload, если они есть
            if payload.get("model"):
                cmd.extend(["--model", payload["model"]])
            if payload.get("diarization"):
                cmd.append("--diarize")
            else:
                cmd.append("--no-diarize")
            if payload.get("method"):
                cmd.extend(["--method", payload["method"]])
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert proc.stdout is not None
            for raw in proc.stdout:
                line = raw.rstrip()
                if not line:
                    continue
                _post(log_url, {"task_id": task_id, "level": _classify(line), "text": line}, secret)
                matches = RE_PROGRESS.findall(line)
                if matches:
                    value = max(0, min(100, int(matches[-1])))
                    _post(prog_url, {"task_id": task_id, "progress": value}, secret)

            code = proc.wait()
            if code == 0:
                transcript = _read_transcript(out)
                _post(done_url, {
                    "task_id": task_id,
                    "transcript": transcript,
                    "words": len(transcript.split()),
                }, secret)
            else:
                _post(err_url, {"task_id": task_id,
                                "error": f"Скрипт завершился с кодом {code} — подробности в журнале"}, secret)
        except Exception as exc:
            _post(err_url, {"task_id": task_id, "error": str(exc)}, secret)


# --------------------------------------------------------------------------- эндпоинты

@app.route("/health")
def health():
    return jsonify({"status": "ok", "port": RUNNER_PORT, "max_concurrent": MAX_CONCURRENT})


@app.route("/run", methods=["POST"])
def run():
    payload = request.get_json(force=True, silent=True) or {}
    if payload.get("secret") != RUNNER_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    if "task_id" not in payload or "script" not in payload:
        return jsonify({"error": "bad payload"}), 400

    threading.Thread(target=_run, args=(payload,), name=f"task-{payload['task_id']}", daemon=True).start()
    return jsonify({"status": "accepted", "task_id": payload["task_id"]}), 202


if __name__ == "__main__":
    print(f"[runner] старт на :{RUNNER_PORT} · max_concurrent={MAX_CONCURRENT}", flush=True)
    app.run(host="0.0.0.0", port=RUNNER_PORT, debug=False, use_reloader=False, threaded=True)
