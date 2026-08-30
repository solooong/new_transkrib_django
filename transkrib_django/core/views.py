"""Представления: страницы транскрибаций + API (frontend + runner-callbacks)."""
import json
import os
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import UploadForm
from .models import Task, TaskLog
from .utils import dispatch_to_runner, get_duration_sec, runner_health


def _is_xhr(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


# --------------------------------------------------------------------------- страницы

@login_required
def dashboard(request):
    """Дашборд: показатели транскрибации и живая таблица задач пользователя."""
    tasks = Task.objects.filter(user=request.user)

    total = tasks.count()
    done_qs = tasks.filter(status=Task.Status.DONE)
    done = done_qs.count()
    active = tasks.filter(status__in=[Task.Status.RUNNING, Task.Status.PENDING]).count()
    errors = tasks.filter(status=Task.Status.ERROR).count()
    minutes = int((done_qs.aggregate(s=Sum("duration_sec"))["s"] or 0) // 60)

    context = {
        "tasks": tasks[:50],
        "kpis": {"total": total, "done": done, "active": active, "errors": errors, "minutes": minutes},
        "runner_online": runner_health(),
    }
    return render(request, "core/dashboard.html", context)


@login_required
def upload_file(request):
    """Загрузка файла и передача задачи в runner."""
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            uploaded = request.FILES["input_file"]
            task.original_name = uploaded.name
            task.size_bytes = uploaded.size
            task.save()

            task.duration_sec = get_duration_sec(task.input_file.path)
            task.save(update_fields=["duration_sec", "updated_at"])

            dispatch_to_runner(task.pk)
            messages.success(request, f"Задача #{task.pk} создана и передана в обработку.")
            return redirect("task_detail", task_id=task.pk)
    else:
        form = UploadForm()
    return render(request, "core/upload.html", {"form": form, "runner_online": runner_health()})


@login_required
def task_detail(request, task_id: int):
    """Страница задачи: статус, транскрипт, журнал, скачивание."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    logs = list(task.logs.order_by("id"))
    last_log_id = logs[-1].pk if logs else 0

    init = json.dumps(
        {"id": task.pk, "status": task.status, "progress": task.progress, "last_log_id": last_log_id},
        ensure_ascii=False,
    )
    context = {
        "task": task,
        "logs": logs[-500:],
        "result_files": task.result_files(),
        "task_init": init,
    }
    return render(request, "core/task_detail.html", context)


@login_required
def download_txt(request, task_id: int):
    """Скачивание результата транскрибации в .txt."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    if not task.has_transcript:
        messages.warning(request, "Транскрипт для этой задачи ещё не готов.")
        return redirect("task_detail", task_id=task.pk)

    content = (
        f"# {task.display_name}\n"
        f"# Модель: {task.model} · Язык: {task.language}"
        f" · Слов: {task.words or '—'}\n"
        f"# Сформировано: {timezone.localtime().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{task.transcript_text}\n"
    )
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{task.txt_filename()}"'
    return response


# --------------------------------------------------------------------------- действия

@login_required
@require_POST
def retry_task(request, task_id: int):
    """Повторная передача задачи в runner."""
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    task.status = Task.Status.PENDING
    task.progress = 0
    task.error = ""
    task.finished_at = None
    task.save(update_fields=["status", "progress", "error", "finished_at", "updated_at"])

    from .utils import add_log

    add_log(task, "── Повторная передача в runner по запросу пользователя ──", "warn")
    dispatch_to_runner(task.pk)

    if _is_xhr(request):
        return JsonResponse({"ok": True, "status": task.status})
    messages.info(request, f"Задача #{task.pk} передана в runner повторно.")
    return redirect("task_detail", task_id=task.pk)


@login_required
@require_POST
def delete_task(request, task_id: int):
    """Удаление задачи вместе с файлом и результатами."""
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


# --------------------------------------------------------------------------- API: frontend

@login_required
def api_tasks(request):
    """Список задач пользователя для live-обновления таблицы."""
    qs = Task.objects.filter(user=request.user)
    tasks = list(qs[:100])
    counts = {"pending": 0, "running": 0, "done": 0, "error": 0}
    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1
    minutes = int((qs.filter(status=Task.Status.DONE).aggregate(s=Sum("duration_sec"))["s"] or 0) // 60)
    return JsonResponse({"tasks": [t.to_api() for t in tasks], "counts": counts, "minutes": minutes})


@login_required
def api_task_logs(request, task_id: int):
    """Дозагрузка журнала с курсором ?since=<id> + актуальный статус и транскрипт."""
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
        "has_transcript": task.has_transcript,
        "logs": [
            {"id": r.pk, "level": r.level, "text": r.text, "t": r.created_at.strftime("%H:%M:%S")}
            for r in rows
        ],
    }
    return JsonResponse(payload)


@login_required
def api_runner_status(request):
    """Доступность runner-а (для индикатора в шапке)."""
    return JsonResponse({"online": runner_health()})


# --------------------------------------------------------------------------- API: runner-callbacks

def _secret_ok(request) -> bool:
    return request.headers.get("X-Runner-Secret") == settings.RUNNER_SECRET


def _get_task_or_none(task_id):
    try:
        return Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return None


@csrf_exempt
@require_POST
def runner_log(request):
    """Runner шлёт строку журнала задачи."""
    if not _secret_ok(request):
        return JsonResponse({"error": "unauthorized"}, status=403)
    data = json.loads(request.body or b"{}")
    task = _get_task_or_none(data.get("task_id"))
    if task is None:
        return JsonResponse({"error": "task not found"}, status=404)
    TaskLog.objects.create(task=task, level=data.get("level", "info"), text=data.get("text", ""))
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def runner_progress(request):
    """Runner обновляет прогресс."""
    if not _secret_ok(request):
        return JsonResponse({"error": "unauthorized"}, status=403)
    data = json.loads(request.body or b"{}")
    progress = max(0, min(100, int(data.get("progress", 0))))
    Task.objects.filter(pk=data.get("task_id")).update(progress=progress)
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def runner_done(request):
    """Runner сообщает об успехе и передаёт текст транскрипта."""
    if not _secret_ok(request):
        return JsonResponse({"error": "unauthorized"}, status=403)
    data = json.loads(request.body or b"{}")
    task = _get_task_or_none(data.get("task_id"))
    if task is None:
        return JsonResponse({"error": "task not found"}, status=404)

    task.status = Task.Status.DONE
    task.progress = 100
    task.error = ""
    task.transcript_text = data.get("transcript", "")
    task.words = data.get("words") or len(task.transcript_text.split())
    task.finished_at = timezone.now()
    task.save()
    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def runner_error(request):
    """Runner сообщает об ошибке."""
    if not _secret_ok(request):
        return JsonResponse({"error": "unauthorized"}, status=403)
    data = json.loads(request.body or b"{}")
    task = _get_task_or_none(data.get("task_id"))
    if task is None:
        return JsonResponse({"error": "task not found"}, status=404)

    task.status = Task.Status.ERROR
    task.error = data.get("error", "Неизвестная ошибка")
    task.save(update_fields=["status", "error", "updated_at"])
    return JsonResponse({"ok": True})
