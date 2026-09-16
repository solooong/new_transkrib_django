from django.urls import path

from .views import (dashboard,upload_file,task_detail,download_txt,download_txt,retry_task,delete_task, 
                        api_tasks,api_task_logs,api_runner_status,runner_log,runner_progress,runner_done,runner_error)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("uploads/", upload_file, name="upload"),
    path("task/<int:task_id>/", task_detail, name="task_detail"),
    path("task/<int:task_id>/download/", download_txt, name="download_txt"),
    path("task/<int:task_id>/retry/", retry_task, name="retry_task"),
    path("task/<int:task_id>/delete/", delete_task, name="delete_task"),
    # API для live-обновлений фронтенда
    path("api/tasks/", api_tasks, name="api_tasks"),
    path("api/task/<int:task_id>/logs/", api_task_logs, name="api_task_logs"),
    path("api/runner-status/", api_runner_status, name="api_runner_status"),
    # Callback-API для Flask-runner'а (секрет в заголовке X-Runner-Secret)
    path("api/runner/log/", runner_log, name="runner_log"),
    path("api/runner/progress/", runner_progress, name="runner_progress"),
    path("api/runner/done/", runner_done, name="runner_done"),
    path("api/runner/error/", runner_error, name="runner_error"),
]
