from django.shortcuts import render

"""Представления для аналитики звонков - импорт аудио."""
import json
import os
import subprocess
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import ImportJob


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
        start_import_job(job.pk)
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
    start_import_job(job.pk)
    return redirect("analytics_job_detail", job_id=job.pk)


def start_import_job(job_id: int):
    """Запуск скрипта импорта в фоне."""
    job = ImportJob.objects.get(pk=job_id)
    job.status = ImportJob.Status.RUNNING
    job.started_at = __import__('django.utils').utils.timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])
    
    # Запуск скрипта в фоне
    script_path = job.script_path
    if not os.path.exists(script_path):
        job.status = ImportJob.Status.ERROR
        job.error = f"Скрипт не найден: {script_path}"
        job.finished_at = __import__('django.utils').utils.timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
        return
    
    cmd = ["python", script_path]
    # Добавляем аргументы
    if job.date_from:
        cmd.extend(["--date-from", job.date_from.isoformat()])
    if job.date_to:
        cmd.extend(["--date-to", job.date_to.isoformat()])
    if job.phone_filter:
        cmd.extend(["--phone", job.phone_filter])
    if job.department_filter:
        cmd.extend(["--department", job.department_filter])
    if job.output_folder:
        cmd.extend(["--output", job.output_folder])
    else:
        cmd.extend(["--output", job.default_output_folder])
    if job.skip_existing:
        cmd.append("--skip-existing")
    if job.min_duration_sec > 0:
        cmd.extend(["--min-duration", str(job.min_duration_sec)])
    
    # Запускаем в фоне
    subprocess.Popen(cmd, cwd=settings.BASE_DIR)


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
