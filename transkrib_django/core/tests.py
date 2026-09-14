"""Unit tests для приложения core."""
import json
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from .models import Task, TaskLog


class TaskModelTest(TestCase):
    """Тесты модели Task."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.task = Task.objects.create(
            user=self.user,
            original_name="test_audio.wav",
            size_bytes=1024 * 1024,  # 1 MB
            duration_sec=120.5,
            language="Русский",
            model="whisper-large-v3",
            status=Task.Status.PENDING,
        )

    def test_task_creation(self):
        """Проверка создания задачи."""
        self.assertEqual(self.task.original_name, "test_audio.wav")
        self.assertEqual(self.task.status, Task.Status.PENDING)
        self.assertEqual(self.task.size_human, "1.0 МБ")
        self.assertEqual(self.task.duration_human, "02:00")

    def test_task_display_name(self):
        """Проверка display_name."""
        self.assertEqual(self.task.display_name, "test_audio.wav")

    def test_task_has_transcript(self):
        """Проверка has_transcript."""
        self.assertFalse(self.task.has_transcript)
        self.task.transcript_text = "Тестовый транскрипт"
        self.task.save()
        self.assertTrue(self.task.has_transcript)

    def test_task_to_api(self):
        """Проверка сериализации в API."""
        api_data = self.task.to_api()
        self.assertIn("id", api_data)
        self.assertIn("file", api_data)
        self.assertIn("status", api_data)
        self.assertEqual(api_data["file"], "test_audio.wav")


class TaskLogModelTest(TestCase):
    """Тесты модели TaskLog."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.task = Task.objects.create(
            user=self.user,
            original_name="test_audio.wav",
            status=Task.Status.RUNNING,
        )

    def test_log_creation(self):
        """Проверка создания лога."""
        log = TaskLog.objects.create(
            task=self.task,
            level=TaskLog.Level.INFO,
            text="Тестовая строка лога",
        )
        self.assertEqual(log.task, self.task)
        self.assertEqual(log.level, "info")
        self.assertEqual(log.text, "Тестовая строка лога")


class CoreViewsTest(TestCase):
    """Тесты views приложения core."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_dashboard_view(self):
        """Проверка дашборда."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Транскрибации")

    def test_upload_view_get(self):
        """Проверка страницы загрузки (GET)."""
        response = self.client.get(reverse("upload"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Новая транскрибация")

    def test_task_detail_view(self):
        """Проверка страницы задачи."""
        task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.DONE,
            transcript_text="Тестовый транскрипт",
        )
        response = self.client.get(reverse("task_detail", args=[task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test.wav")

    def test_download_txt_view(self):
        """Проверка скачивания транскрипта."""
        task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.DONE,
            transcript_text="Тестовый транскрипт",
        )
        response = self.client.get(reverse("download_txt", args=[task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_api_tasks_view(self):
        """Проверка API списка задач."""
        Task.objects.create(
            user=self.user,
            original_name="test1.wav",
            status=Task.Status.DONE,
        )
        Task.objects.create(
            user=self.user,
            original_name="test2.wav",
            status=Task.Status.RUNNING,
        )
        response = self.client.get(reverse("api_tasks"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("tasks", data)
        self.assertIn("counts", data)
        self.assertEqual(len(data["tasks"]), 2)

    def test_api_task_logs_view(self):
        """Проверка API логов задачи."""
        task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.RUNNING,
        )
        TaskLog.objects.create(task=task, level="info", text="Лог 1")
        TaskLog.objects.create(task=task, level="ok", text="Лог 2")
        
        response = self.client.get(reverse("api_task_logs", args=[task.pk]))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("logs", data)
        self.assertEqual(len(data["logs"]), 2)

    def test_retry_task_view(self):
        """Проверка повторного запуска задачи."""
        task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.ERROR,
            error="Тестовая ошибка",
        )
        response = self.client.post(reverse("retry_task", args=[task.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.PENDING)

    def test_delete_task_view(self):
        """Проверка удаления задачи."""
        task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.DONE,
        )
        response = self.client.post(reverse("delete_task", args=[task.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())


class RunnerCallbackViewsTest(TestCase):
    """Тесты callback API для runner'а."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.task = Task.objects.create(
            user=self.user,
            original_name="test.wav",
            status=Task.Status.RUNNING,
        )
        self.secret = "test-secret"
        # Временно изменяем настройку для теста
        from django.conf import settings
        self.original_secret = settings.RUNNER_SECRET
        settings.RUNNER_SECRET = self.secret

    def tearDown(self):
        from django.conf import settings
        settings.RUNNER_SECRET = self.original_secret

    def test_runner_log_callback(self):
        """Проверка callback для лога."""
        response = self.client.post(
            reverse("runner_log"),
            data=json.dumps({
                "task_id": self.task.pk,
                "level": "info",
                "text": "Тестовый лог",
            }),
            content_type="application/json",
            HTTP_X_RUNNER_SECRET=self.secret,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TaskLog.objects.filter(task=self.task, text="Тестовый лог").exists())

    def test_runner_progress_callback(self):
        """Проверка callback для прогресса."""
        response = self.client.post(
            reverse("runner_progress"),
            data=json.dumps({
                "task_id": self.task.pk,
                "progress": 50,
            }),
            content_type="application/json",
            HTTP_X_RUNNER_SECRET=self.secret,
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.progress, 50)

    def test_runner_done_callback(self):
        """Проверка callback для завершения."""
        response = self.client.post(
            reverse("runner_done"),
            data=json.dumps({
                "task_id": self.task.pk,
                "transcript": "Тестовый транскрипт",
                "words": 3,
            }),
            content_type="application/json",
            HTTP_X_RUNNER_SECRET=self.secret,
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)
        self.assertEqual(self.task.transcript_text, "Тестовый транскрипт")
        self.assertEqual(self.task.words, 3)

    def test_runner_error_callback(self):
        """Проверка callback для ошибки."""
        response = self.client.post(
            reverse("runner_error"),
            data=json.dumps({
                "task_id": self.task.pk,
                "error": "Тестовая ошибка",
            }),
            content_type="application/json",
            HTTP_X_RUNNER_SECRET=self.secret,
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.ERROR)
        self.assertEqual(self.task.error, "Тестовая ошибка")

    def test_runner_callback_unauthorized(self):
        """Проверка отказа без секрета."""
        response = self.client.post(
            reverse("runner_log"),
            data=json.dumps({
                "task_id": self.task.pk,
                "level": "info",
                "text": "Тест",
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
