"""URL-маршруты для аналитики звонков."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.analytics_dashboard, name="analytics_dashboard"),
    path("create/", views.create_import_job, name="analytics_create"),
    path("job/<int:job_id>/", views.job_detail, name="analytics_job_detail"),
    path("job/<int:job_id>/start/", views.start_job, name="analytics_start_job"),
    # API
    path("api/jobs/", views.api_import_jobs, name="analytics_api_jobs"),
    path("api/job/<int:job_id>/status/", views.api_job_status, name="analytics_api_job_status"),
]
