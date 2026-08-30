"""Создаёт демо-пользователя и примеры транскрибаций (без мониторинга).

Идемпотентна: безопасна к повторному запуску на каждом старте контейнера.
"""
import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Создаёт демо-пользователя (ADMIN_USERNAME/ADMIN_PASSWORD) и примеры транскрибаций"

    def handle(self, *args, **options):
        self._ensure_admin()
        self._ensure_tasks()
        self.stdout.write(self.style.SUCCESS("seed_demo: готово"))

    def _ensure_admin(self):
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "admin")
        if User.objects.filter(username=username).exists():
            return
        User.objects.create_superuser(username, f"{username}@transkrib.local", password)
        self.stdout.write(f"создан пользователь {username}/{password}")

    def _ensure_tasks(self):
        from core.models import Task, TaskLog

        if Task.objects.exists():
            return

        admin = User.objects.get(username=os.environ.get("ADMIN_USERNAME", "admin"))
        now = timezone.now()

        def add_logs(task, lines, start):
            objs = [TaskLog(task=task, level=lvl, text=txt) for _, lvl, txt in lines]
            created = TaskLog.objects.bulk_create(objs)
            for (offset, _, _), obj in zip(lines, created):
                TaskLog.objects.filter(pk=obj.pk).update(created_at=start + timedelta(seconds=offset))

        # 1) завершённая транскрибация с готовым текстом
        t1 = Task.objects.create(
            user=admin,
            input_file="uploads/demo_интервью_о_продукте.wav",
            original_name="интервью_о_продукте.wav",
            size_bytes=312 * 1024 * 1024,
            duration_sec=34 * 60,
            language="Русский",
            model="whisper-large-v3",
            diarization=True,
            status=Task.Status.DONE,
            progress=100,
            words=4310,
            transcript_text=(
                "Спикер 1: Мы провели четырнадцать глубинных интервью за последние две недели.\n"
                "Спикер 2: Основная проблема была в том, что пользователи не понимали, с чего начать.\n"
                "Спикер 1: Смотри, метрики удержания выросли на девять процентов после редизайна.\n"
                "Спикер 2: Это классическая ошибка — сначала строить решение, а потом искать проблему.\n"
                "Спикер 1: Согласен. Давай разобьём задачу на три этапа и оценим каждый отдельно."
            ),
            finished_at=now - timedelta(hours=2),
        )
        Task.objects.filter(pk=t1.pk).update(created_at=now - timedelta(hours=2, minutes=9))
        start = now - timedelta(hours=2, minutes=9)
        add_logs(
            t1,
            [
                (0, "info", "[runner] запуск: python 1.py --input … --output …"),
                (3, "info", "[ffmpeg] извлечение аудиодорожки: 44 100 Гц → mono 16 кГц"),
                (10, "info", "[chunk] обработан фрагмент #12 из 85 (14%)"),
                (60, "info", "[chunk] обработан фрагмент #40 из 85 (47%)"),
                (180, "info", "[chunk] обработан фрагмент #71 из 85 (84%)"),
                (320, "ok", "[export] слов распознано: 4 310 · CER 2.1%"),
                (322, "ok", "[runner] транскрипт передан в Django · процесс завершён с кодом 0"),
            ],
            start,
        )

        # 2) задача с ошибкой CUDA OOM
        t2 = Task.objects.create(
            user=admin,
            input_file="uploads/demo_вебинар.mp3",
            original_name="вебинар_onboarding.mp3",
            size_bytes=96 * 1024 * 1024,
            duration_sec=63 * 60,
            language="English",
            model="whisper-large-v3",
            diarization=True,
            status=Task.Status.ERROR,
            progress=63,
            error="Скрипт завершился с кодом 1 — CUDA out of memory (не удалось выделить 6.2 ГиБ).",
        )
        Task.objects.filter(pk=t2.pk).update(created_at=now - timedelta(hours=5))
        add_logs(
            t2,
            [
                (0, "info", "[runner] запуск: python 1.py --input … --output …"),
                (8, "info", "[chunk] обработан фрагмент #30 из 48 (63%)"),
                (14, "warn", "[gpu] VRAM занято 21.9 / 22.4 ГБ · утилизация 100%"),
                (16, "err", "RuntimeError: CUDA out of memory: tried to allocate 6.20 GiB"),
                (16, "err", "[runner] скрипт завершился с кодом 1 — подробности в журнале"),
            ],
            now - timedelta(hours=5),
        )

        # 3) задача в очереди
        t3 = Task.objects.create(
            user=admin,
            input_file="uploads/demo_дейли.m4a",
            original_name="дейли_команды.m4a",
            size_bytes=11 * 1024 * 1024,
            duration_sec=12 * 60,
            language="Русский",
            model="whisper-base",
            diarization=False,
            status=Task.Status.PENDING,
        )
        Task.objects.filter(pk=t3.pk).update(created_at=now - timedelta(minutes=6))
        add_logs(t3, [(0, "info", "Задача поставлена в очередь · позиция 1")], now - timedelta(minutes=6))

        self.stdout.write("транскрибации: создано 3 демо-задачи")
