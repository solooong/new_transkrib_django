"""Unit tests для приложения analytics."""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from .models import ImportJob


class ImportJobModelTest(TestCase):
    """Тесты модели ImportJob."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.job = ImportJob.objects.create(
            user=self.user,
            source=ImportJob.SourceType.GAZOIL,
            date_from="2024-01-01",
            date_to="2024-01-31",
            phone_filter="+79991234567",
        )

    def test_job_creation(self):
        """Проверка создания задания."""
        self.assertEqual(self.job.source, "gazoil")
        self.assertEqual(self.job.status, ImportJob.Status.PENDING)
        self.assertEqual(self.job.get_source_display(), "ГазОйл")

    def test_script_path(self):
        """Проверка пути к скрипту."""
        self.assertIn("import_from_ats_gazoil.py", self.job.script_path)

    def test_to_api(self):
        """Проверка сериализации в API."""
        api_data = self.job.to_api()
        self.assertIn("id", api_data)
        self.assertIn("source", api_data)
        self.assertEqual(api_data["source"], "gazoil")


class AnalyticsViewsTest(TestCase):
    """Тесты views приложения analytics."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")

    def test_dashboard_view(self):
        """Проверка дашборда аналитики."""
        response = self.client.get(reverse("analytics_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_create_import_view_get(self):
        """Проверка страницы создания задания (GET)."""
        response = self.client.get(reverse("analytics_create_import"))
        self.assertEqual(response.status_code, 200)

    def test_job_detail_view(self):
        """Проверка страницы задания."""
        job = ImportJob.objects.create(
            user=self.user,
            source=ImportJob.SourceType.GAZOIL,
            status=ImportJob.Status.DONE,
        )
        response = self.client.get(reverse("analytics_job_detail", args=[job.pk]))
        self.assertEqual(response.status_code, 200)

    def test_api_import_jobs_view(self):
        """Проверка API списка заданий."""
        ImportJob.objects.create(
            user=self.user,
            source=ImportJob.SourceType.GAZOIL,
            status=ImportJob.Status.DONE,
        )
        response = self.client.get(reverse("analytics_api_import_jobs"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("jobs", data)
