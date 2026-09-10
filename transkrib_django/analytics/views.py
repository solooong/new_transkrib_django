from django.shortcuts import render

"""Представления для аналитики звонков - импорт аудио."""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ImportJob
from ..core.background import launch_background_script


@login_required
def analytics_dashboard(request):
    """Дашборд аналитики звонков."""
    jobs = ImportJob.objects.filter(user=request.user)[:50]
    context = {
        "jobs": jobs,
        "sources": ImportJob.SourceType.choices,
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
def create_import_job(request):
    """Создание задания импорта."""
    if request.method == "POST":
        job = ImportJob(
            user=request.user,
            source=request.POST.get("source"),
            date_from=request.POST.get("date_from") or None,
            date_to=request.POST.get("date_to") or None,
            phone_filter=request.POST.get("phone_filter", ""),
            department_filter=request.POST.get("department_filter", ""),
            skip_existing=request.POST.get("skip_existing") == "on",
            min_duration_sec=int(request.POST.get("min_duration_sec", 0)),
            output_folder=request.POST.get("output_folder", "").strip(),
        )
        job.save()
        _launch(job.pk)
        messages.success(request, f"Задание импорта #{job.pk} создано и запущено.")
        return redirect("analytics_job_detail", job_id=job.pk)
    
    context = {
        "sources": ImportJob.SourceType.choices,
    }
    return render(request, "analytics/create_import.html", context)


@login_required
def job_detail(request, job_id: int):
    """Страница задания импорта."""
    job = get_object_or_404(ImportJob, pk=job_id, user=request.user)
    init = json.dumps({
        "id": job.pk,
        "status": job.status,
        "progress": job.progress,
    }, ensure_ascii=False)
    context = {
        "job": job,
        "job_init": init,
    }
    return render(request, "analytics/job_detail.html", context)


@login_required
@require_POST
def start_job(request, job_id: int):
    """Запуск задания импорта."""
    job = get_object_or_404(ImportJob, pk=job_id, user=request.user)
    if job.status == ImportJob.Status.RUNNING:
        return JsonResponse({"error": "Already running"}, status=400)
    _launch(job.pk)
    return redirect("analytics_job_detail", job_id=job.pk)


def _launch(task_id: int) -> None:
    """Устанавливает статус RUNNING и запускает скрипт (общая логика)."""
    from .models import ImportJob

    job = ImportJob.objects.get(pk=task_id)
    job.status = ImportJob.Status.RUNNING
    job.started_at = timezone.now()
    ok, error = launch_background_script(job.script_path, _build_args(job))
    if not ok:
        job.status = ImportJob.Status.ERROR
        job.error = error
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
        return
    job.save(update_fields=["status", "started_at", "updated_at"])


def _build_args(job) -> list[str]:
    args: list[str] = []
    if job.date_from:
        args.extend(["--date-from", job.date_from.isoformat()])
    if job.date_to:
        args.extend(["--date-to", job.date_to.isoformat()])
    if job.phone_filter:
        args.extend(["--phone", job.phone_filter])
    if job.department_filter:
        args.extend(["--department", job.department_filter])
    if job.output_folder:
        args.extend(["--output", job.output_folder])
    else:
        args.extend(["--output", job.default_output_folder])
    if job.skip_existing:
        args.append("--skip-existing")
    if job.min_duration_sec > 0:
        args.extend(["--min-duration", str(job.min_duration_sec)])
    return args


@login_required
def api_import_jobs(request):
    """API для списка заданий импорта."""
    jobs = ImportJob.objects.filter(user=request.user)[:100]
    return JsonResponse({"jobs": [j.to_api() for j in jobs]})


@login_required
def api_job_status(request, job_id: int):
    """API для статуса задания импорта."""
    job = get_object_or_404(ImportJob, pk=job_id, user=request.user)
    return JsonResponse(job.to_api())
