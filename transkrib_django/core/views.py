"""Представления: страницы + JSON API для live-обновлений интерфейса."""
import json
import os
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import FileResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import UploadForm
from .models import SystemMetric, Task
from .utils import get_duration_sec, start_transcription


def _is_xhr(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


# --------------------------------------------------------------------------- страницы

@login_required
def dashboard(request):
    """Дашборд: KPI, метрики системы, живая таблица задач."""
    tasks = Task.objects.filter(user=request.user)

    done_qs = tasks.filter(status=Task.Status.DONE)
    total = tasks.count()
    done = done_qs.count()
    running = tasks.filter(status=Task.Status.RUNNING).count()
    pending = tasks.filter(status=Task.Status.PENDING).count()
    minutes = int((done_qs.aggregate(s=Sum("duration_sec"))["s"] or 0) // 60)

    history = list(SystemMetric.objects.order_by("-id")[:180])[::-1]
    current = history[-1].to_api() if history else None

    initial = {"current": current, "history": [m.to_api() for m in history]}

    context = {
        "tasks": tasks[:50],
        "kpis": {"total": total, "done": done, "running": running, "pending": pending, "minutes": minutes},
        "initial_json": json.dumps(initial, ensure_ascii=False),
    }
    return render(request, "core/dashboard.html", context)


@login_required
def upload_file(request):
    """Загрузка файла и запуск транскрибации в фоне."""
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            uploaded = request.FILES["input_file"]
            task.original_name = uploaded.name
            task.size_bytes = uploaded.size
            
            # Сохраняем output_path из формы
            task.output_path = request.POST.get("output_path", "").strip()
            
            task.save()

            task.duration_sec = get_duration_sec(task.input_file.path)
            task.save(update_fields=["duration_sec", "updated_at"])

            start_transcription(task.pk)
            messages.success(request, f"Задача #{task.pk} создана и поставлена в очередь.")
            return redirect("task_detail", task_id=task.pk)
    else:
        form = UploadForm()
    return render(request, "core/upload.html", {"form": form})


@login_required
def task_detail(request, task_id: int):
    """Страница задачи: статус, журнал, результаты."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    logs = list(task.logs.order_by("id"))
    last_log_id = logs[-1].pk if logs else 0

    init = json.dumps(
        {"id": task.pk, "status": task.status, "progress": task.progress, "last_log_id": last_log_id},
        ensure_ascii=False,
    )
    context = {
        "task": task,
        "logs": logs[-500:],  # последние 500 строк для первой отрисовки
        "result_files": task.result_files(),
        "task_init": init,
    }
    return render(request, "core/task_detail.html", context)


@login_required
def download_result(request, task_id: int, filename: str):
    """Скачивание файла результатов с защитой от path traversal."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)

    folder = os.path.realpath(task.result_folder())
    media_root = os.path.realpath(settings.MEDIA_ROOT)
    if not folder.startswith(media_root + os.sep):
        return JsonResponse({"error": "invalid folder"}, status=400)

    safe_name = os.path.basename(filename)
    path = os.path.realpath(os.path.join(folder, safe_name))
    if not path.startswith(folder + os.sep) or not os.path.isfile(path):
        return JsonResponse({"error": "file not found"}, status=404)

    return FileResponse(open(path, "rb"), as_attachment=True, filename=safe_name)


# --------------------------------------------------------------------------- действия

@login_required
@require_POST
def retry_task(request, task_id: int):
    """Повторный запуск упавшей (или завершённой) задачи."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    task.status = Task.Status.PENDING
    task.progress = 0
    task.error = ""
    task.finished_at = None
    task.save(update_fields=["status", "progress", "error", "finished_at", "updated_at"])

    from .utils import add_log

    add_log(task, "── Повторный запуск по запросу пользователя ──", "warn")
    start_transcription(task.pk)

    if _is_xhr(request):
        return JsonResponse({"ok": True, "status": task.status})
    messages.info(request, f"Задача #{task.pk} запущена повторно.")
    return redirect("task_detail", task_id=task.pk)


@login_required
@require_POST
def delete_task(request, task_id: int):
    """Удаление задачи вместе с загруженным файлом и результатами."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)

    try:
        if task.input_file:
            task.input_file.delete(save=False)
    except Exception:
        pass

    folder = os.path.realpath(task.result_folder())
    media_root = os.path.realpath(settings.MEDIA_ROOT)
    if folder.startswith(media_root + os.sep) and os.path.isdir(folder):
        shutil.rmtree(folder, ignore_errors=True)

    task.delete()

    if _is_xhr(request):
        return JsonResponse({"ok": True})
    messages.success(request, f"Задача #{task_id} удалена.")
    return redirect("dashboard")


# --------------------------------------------------------------------------- API

@login_required
def api_metrics(request):
    """Текущие метрики + история для графиков (polling каждые 2 с)."""
    history = list(SystemMetric.objects.order_by("-id")[:180])[::-1]
    payload = {
        "current": history[-1].to_api() if history else None,
        "history": [m.to_api() for m in history],
    }
    return JsonResponse(payload)


@login_required
def api_tasks(request):
    """Список задач пользователя для live-обновления таблицы."""
    tasks = Task.objects.filter(user=request.user)[:100]
    counts = {"pending": 0, "running": 0, "done": 0, "error": 0}
    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1
    return JsonResponse({"tasks": [t.to_api() for t in tasks], "counts": counts})


@login_required
def api_task_logs(request, task_id: int):
    """Дозагрузка журнала с курсором ?since=<id> + актуальный статус."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    try:
        since = int(request.GET.get("since", 0))
    except (TypeError, ValueError):
        since = 0

    rows = task.logs.filter(id__gt=since).order_by("id")[:200]
    payload = {
        "status": task.status,
        "status_label": task.get_status_display(),
        "progress": task.progress,
        "error": task.error,
        "logs": [
            {
                "id": r.pk,
                "level": r.level,
                "text": r.text,
                "t": r.created_at.strftime("%H:%M:%S"),
            }
            for r in rows
        ],
    }
    return JsonResponse(payload)
