"""Общий запуск внешних скриптов в фоне (для импорта и оценки звонков).

Логика запуска вынесена сюда, чтобы analytics/evaluation не дублировали
проверку существования скрипта и создание команды subprocess.
"""
import os
import subprocess

from django.conf import settings


def launch_background_script(script_path: str, extra_args=None) -> tuple[bool, str | None]:
    """Проверяет существование скрипта и запускает его в фоне.

    Аргументы:
        script_path — полный путь к внешнему скрипту (scripts/...).
        extra_args  — дополнительные аргументы CLI для скрипта.

    Возвращает ``(ok, error)``: при успехе ``error`` равно None;
    при отсутствии файла — ``ok=False`` и строка с ошибкой.
    """
    if not os.path.exists(script_path):
        return False, f"Скрипт не найден: {script_path}"

    cmd = ["python", script_path]
    if extra_args:
        cmd.extend(extra_args)

    # Запуск в фоне относительно корня проекта (где лежат скрипты).
    subprocess.Popen(cmd, cwd=settings.BASE_DIR)
    return True, None
