"""Unit tests для Flask-runner'а."""
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.test.client import Client as DjangoClient
<<<<<<< HEAD
# Импортируем runner для тестирования
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import runner as runner
=======

# Импортируем runner для тестирования
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import runner
>>>>>>> 02fb2d110c23c3aa2cea55d730a11936de07e850


class RunnerFlaskTest(TestCase):
    """Тесты Flask-runner'а."""

    def setUp(self):
        """Настройка тестового клиента Flask."""
        runner.app.config["TESTING"] = True
        self.client = runner.app.test_client()
        self.secret = "test-secret"
        runner.RUNNER_SECRET = self.secret

    def test_health_endpoint(self):
        """Проверка эндпоинта /health."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")
        self.assertIn("port", data)

    def test_run_endpoint_without_secret(self):
        """Проверка отказа без секрета."""
        response = self.client.post(
            "/run",
            data=json.dumps({"task_id": 1, "script": "test.py"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_run_endpoint_with_wrong_secret(self):
        """Проверка отказа с неправильным секретом."""
        response = self.client.post(
            "/run",
            data=json.dumps({"task_id": 1, "script": "test.py", "secret": "wrong"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_run_endpoint_missing_fields(self):
        """Проверка отказа при отсутствии обязательных полей."""
        response = self.client.post(
            "/run",
            data=json.dumps({"task_id": 1, "secret": self.secret}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("runner.subprocess.Popen")
    @patch("runner._post")
    def test_run_endpoint_accepted(self, mock_post, mock_popen):
        """Проверка принятия задачи."""
        mock_popen.return_value = MagicMock()
        
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"# test script")
            script_path = f.name
        
        try:
            response = self.client.post(
                "/run",
                data=json.dumps({
                    "task_id": 1,
                    "script": script_path,
                    "input": "/tmp/test.wav",
                    "output_dir": "/tmp/output",
                    "callback_base": "http://localhost:8000",
                    "secret": self.secret,
                }),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 202)
            data = json.loads(response.data)
            self.assertEqual(data["status"], "accepted")
            self.assertEqual(data["task_id"], 1)
        finally:
            os.unlink(script_path)


class RunnerHelpersTest(TestCase):
    """Тесты вспомогательных функций runner'а."""

    def test_classify_error(self):
        """Проверка классификации ошибок."""
        self.assertEqual(runner._classify("Error: something went wrong"), "err")
        self.assertEqual(runner._classify("Traceback (most recent call last)"), "err")
        self.assertEqual(runner._classify("Failed to process"), "err")

    def test_classify_warning(self):
        """Проверка классификации предупреждений."""
        self.assertEqual(runner._classify("Warning: low memory"), "warn")
        self.assertEqual(runner._classify("Skip: file not found"), "warn")

    def test_classify_success(self):
        """Проверка классификации успеха."""
        self.assertEqual(runner._classify("Done processing"), "ok")
        self.assertEqual(runner._classify("Success: completed"), "ok")
        self.assertEqual(runner._classify("Process finished"), "ok")

    def test_classify_info(self):
        """Проверка классификации информации."""
        self.assertEqual(runner._classify("Starting process"), "info")
        self.assertEqual(runner._classify("Loading model"), "info")

    def test_read_transcript_priority(self):
        """Проверка приоритета чтения транскрипта."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Создаём файлы в разном порядке
            with open(os.path.join(tmpdir, "other.txt"), "w") as f:
                f.write("Другой файл")
            
            with open(os.path.join(tmpdir, "transcript.txt"), "w") as f:
                f.write("Основной транскрипт")
            
            result = runner._read_transcript(tmpdir)
            self.assertEqual(result, "Основной транскрипт")

    def test_read_transcript_cyrillic(self):
        """Проверка чтения кириллического файла."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "транскрипт.txt"), "w", encoding="utf-8") as f:
                f.write("Русский транскрипт")
            
            result = runner._read_transcript(tmpdir)
            self.assertEqual(result, "Русский транскрипт")

    def test_read_transcript_not_found(self):
        """Проверка отсутствия транскрипта."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner._read_transcript(tmpdir)
            self.assertEqual(result, "")

    def test_read_transcript_nonexistent_dir(self):
        """Проверка несуществующей директории."""
        result = runner._read_transcript("/nonexistent/path")
        self.assertEqual(result, "")
