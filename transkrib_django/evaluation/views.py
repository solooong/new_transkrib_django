from django.shortcuts import render

"""Представления для оценки звонков."""
import json
import os
import subprocess
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import EvaluationJob


@login_required
def evaluation_dashboard(request):
    """Дашборд оценки звонков."""
    jobs = EvaluationJob.objects.filter(user=request.user)[:50]
    context = {
        "jobs": jobs,
        "sources": EvaluationJob.SourceType.choices,
    }
    return render(request, "evaluation/dashboard.html", context)


@login_required
def create_evaluation_job(request):
    """Создание задания оценки."""
    if request.method == "POST":
        job = EvaluationJob(
            user=request.user,
            source=request.POST.get("source"),
            date_from=request.POST.get("date_from") or None,
            date_to=request.POST.get("date_to") or None,
            input_folder=request.POST.get("input_folder", "").strip(),
            output_folder=request.POST.get("output_folder", "").strip(),
            rebuild_excel_only=request.POST.get("rebuild_excel_only") == "on",
            eval_only=request.POST.get("eval_only") == "on",
        )
        job.save()
        start_evaluation_job(job.pk)
        messages.success(request, f"Задание оценки #{job.pk} создано и запущено.")
        return redirect("evaluation_job_detail", job_id=job.pk)
    
    context = {
        "sources": EvaluationJob.SourceType.choices,
    }
    return render(request, "evaluation/create_evaluation.html", context)


@login_required
def job_detail(request, job_id: int):
    """Страница задания оценки."""
    job = get_object_or_404(EvaluationJob, pk=job_id, user=request.user)
    init = json.dumps({
        "id": job.pk,
        "status": job.status,
        "progress": job.progress,
    }, ensure_ascii=False)
    context = {
        "job": job,
        "job_init": init,
    }
    return render(request, "evaluation/job_detail.html", context)


@login_required
@require_POST
def start_job(request, job_id: int):
    """Запуск задания оценки."""
    job = get_object_or_404(EvaluationJob, pk=job_id, user=request.user)
    if job.status == EvaluationJob.Status.RUNNING:
        return JsonResponse({"error": "Already running"}, status=400)
    start_evaluation_job(job.pk)
    return redirect("evaluation_job_detail", job_id=job.pk)


def start_evaluation_job(job_id: int):
    """Запуск скрипта оценки в фоне."""
    job = EvaluationJob.objects.get(pk=job_id)
    job.status = EvaluationJob.Status.RUNNING
    job.started_at = __import__('django.utils').utils.timezone.now()
    job.save(update_fields=["status", "started_at", "updated_at"])
    
    # Запуск скрипта в фоне
    script_path = job.script_path
    if not os.path.exists(script_path):
        job.status = EvaluationJob.Status.ERROR
        job.error = f"Скрипт не найден: {script_path}"
        job.finished_at = __import__('django.utils').utils.timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
        return
    
    cmd = ["python", script_path]
    # Добавляем аргументы согласно логике main из ТЗ
    if job.rebuild_excel_only:
        cmd.append("--rebuild-excel")
    elif job.eval_only:
        cmd.append("--eval-only")
    
    # Запускаем в фоне
    subprocess.Popen(cmd, cwd=settings.BASE_DIR)


@login_required
def api_evaluation_jobs(request):
    """API для списка заданий оценки."""
    jobs = EvaluationJob.objects.filter(user=request.user)[:100]
    return JsonResponse({"jobs": [j.to_api() for j in jobs]})


@login_required
def api_job_status(request, job_id: int):
    """API для статуса задания оценки."""
    job = get_object_or_404(EvaluationJob, pk=job_id, user=request.user)
    return JsonResponse(job.to_api())
