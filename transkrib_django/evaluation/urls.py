"""URL-маршруты для оценки звонков."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.evaluation_dashboard, name="evaluation_dashboard"),
    path("create/", views.create_evaluation_job, name="evaluation_create"),
    path("job/<int:job_id>/", views.job_detail, name="evaluation_job_detail"),
    path("job/<int:job_id>/start/", views.start_job, name="evaluation_start_job"),
    # API
    path("api/jobs/", views.api_evaluation_jobs, name="evaluation_api_jobs"),
    path("api/job/<int:job_id>/status/", views.api_job_status, name="evaluation_api_job_status"),
]
