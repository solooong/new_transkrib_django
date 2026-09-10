from django.shortcuts import render

"""Представления для оценки звонков."""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import EvaluationJob
from core.background import launch_background_script


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
        _launch(job.pk)
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
    _launch(job.pk)
    return redirect("evaluation_job_detail", job_id=job.pk)


def _launch(task_id: int) -> None:
    """Устанавливает статус RUNNING и запускает скрипт (общая логика)."""
    from .models import EvaluationJob

    job = EvaluationJob.objects.get(pk=task_id)
    job.status = EvaluationJob.Status.RUNNING
    job.started_at = timezone.now()
    ok, error = launch_background_script(job.script_path, _build_args(job))
    if not ok:
        job.status = EvaluationJob.Status.ERROR
        job.error = error
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error", "finished_at", "updated_at"])
        return
    job.save(update_fields=["status", "started_at", "updated_at"])


def _build_args(job) -> list[str]:
    args: list[str] = []
    if job.rebuild_excel_only:
        args.append("--rebuild-excel")
    elif job.eval_only:
        args.append("--eval-only")
    return args


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
