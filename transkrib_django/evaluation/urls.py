"""URL-маршруты для оценки звонков."""
from django.urls import path

from  .views import api_job_status , api_evaluation_jobs , start_job , job_detail , create_evaluation_job, evaluation_dashboard

urlpatterns = [
    path("", evaluation_dashboard, name="evaluation_dashboard"),
    path("create/", create_evaluation_job, name="evaluation_create"),
    path("job/<int:job_id>/", job_detail, name="evaluation_job_detail"),
    path("job/<int:job_id>/start/", start_job, name="evaluation_start_job"),
    # API
    path("api/jobs/", api_evaluation_jobs, name="evaluation_api_jobs"),
    path("api/job/<int:job_id>/status/", api_job_status, name="evaluation_api_job_status"),
]
