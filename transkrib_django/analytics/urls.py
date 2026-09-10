"""URL-маршруты для аналитики звонков."""
from django.urls import path

from .views import (analytics_dashboard,create_import_job,job_detail, start_job, api_import_jobs, api_job_status)

urlpatterns = [
    path("", analytics_dashboard, name="analytics_dashboard"),
    path("create/", create_import_job, name="analytics_create"),
    path("job/<int:job_id>/", job_detail, name="analytics_job_detail"),
    path("job/<int:job_id>/start/", start_job, name="analytics_start_job"),
    # API
    path("api/jobs/", api_import_jobs, name="analytics_api_jobs"),
    path("api/job/<int:job_id>/status/", api_job_status, name="analytics_api_job_status"),
]
