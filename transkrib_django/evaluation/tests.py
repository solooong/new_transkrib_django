"""Unit tests для приложения evaluation."""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from .models import EvaluationJob


class EvaluationJobModelTest(TestCase):
    """Тесты модели EvaluationJob."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.job = EvaluationJob.objects.create(
            user=self.user,
            source=EvaluationJob.SourceType.GAZOIL,
        )

    def test_job_creation(self):
        """Проверка создания задания."""
        self.assertEqual(self.job.source, "gazoil")
        self.assertEqual(self.job.status, EvaluationJob.Status.PENDING)

    def test_script_path(self):
        """Проверка пути к скрипту."""
        self.assertIn("final_report_gazoil.py", self.job.script_path)

    def test_to_api(self):
        """Проверка сериализации в API."""
        api_data = self.job.to_api()
        self.assertIn("id", api_data)
        self.assertIn("source", api_data)


class EvaluationViewsTest(TestCase):
    """Тесты views приложения evaluation."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_dashboard_view(self):
        """Проверка дашборда оценки."""
        response = self.client.get(reverse("evaluation_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_create_evaluation_view_get(self):
        """Проверка страницы создания задания (GET)."""
        response = self.client.get(reverse("evaluation_create"))
        self.assertEqual(response.status_code, 200)

    def test_job_detail_view(self):
        """Проверка страницы задания."""
        job = EvaluationJob.objects.create(
            user=self.user,
            source=EvaluationJob.SourceType.GAZOIL,
            status=EvaluationJob.Status.DONE,
        )
        response = self.client.get(reverse("evaluation_job_detail", args=[job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_api_evaluation_jobs_view(self):
        """Проверка API списка заданий."""
        EvaluationJob.objects.create(
            user=self.user,
            source=EvaluationJob.SourceType.GAZOIL,
            status=EvaluationJob.Status.DONE,
        )
        response = self.client.get(reverse("evaluation_api_jobs"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("jobs", data)
