from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_file, name="upload"),
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("task/<int:task_id>/retry/", views.retry_task, name="retry_task"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    path("task/<int:task_id>/download/<str:filename>/", views.download_result, name="download_result"),
    # API для live-обновлений (см. static/core/js/*.js)
    path("api/metrics/", views.api_metrics, name="api_metrics"),
    path("api/tasks/", views.api_tasks, name="api_tasks"),
    path("api/task/<int:task_id>/logs/", views.api_task_logs, name="api_task_logs"),
]
