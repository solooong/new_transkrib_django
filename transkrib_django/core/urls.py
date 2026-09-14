from django.urls import path

from .views import (dashboard,upload_file,task_detail,download_txt,download_txt,retry_task,delete_task, 
                        api_tasks,api_task_logs,api_runner_status,runner_log,runner_progress,runner_done,runner_error)

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_file, name="upload"),
    path("task/<int:task_id>/", views.task_detail, name="task_detail"),
    path("task/<int:task_id>/download/", views.download_txt, name="download_txt"),
    path("task/<int:task_id>/retry/", views.retry_task, name="retry_task"),
    path("task/<int:task_id>/delete/", views.delete_task, name="delete_task"),
    # API для live-обновлений фронтенда
    path("api/tasks/", views.api_tasks, name="api_tasks"),
    path("api/task/<int:task_id>/logs/", views.api_task_logs, name="api_task_logs"),
    path("api/runner-status/", views.api_runner_status, name="api_runner_status"),
    # Callback-API для Flask-runner'а (секрет в заголовке X-Runner-Secret)
    path("api/runner/log/", views.runner_log, name="runner_log"),
    path("api/runner/progress/", views.runner_progress, name="runner_progress"),
    path("api/runner/done/", views.runner_done, name="runner_done"),
    path("api/runner/error/", views.runner_error, name="runner_error"),
]
