"""Создаёт демо-пользователя admin/admin, примеры задач и историю метрик.

Идемпотентна: безопасна к повторному запуску на каждом старте контейнера.
"""
import math
import os
import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Создаёт демо-пользователя (admin/admin) и примеры задач"

    def handle(self, *args, **options):
        self._ensure_admin()
        self._ensure_metrics()
        self._ensure_tasks()
        self.stdout.write(self.style.SUCCESS("seed_demo: готово"))

    # ------------------------------------------------------------------
    def _ensure_admin(self):
        if User.objects.filter(username="admin").exists():
            return
        User.objects.create_superuser("admin", "admin@transkrib.local", "admin")
        self.stdout.write("создан пользователь admin/admin")

    def _ensure_metrics(self):
        from core.models import SystemMetric

        if SystemMetric.objects.exists():
            return

        rnd = random.Random(42)
        now = timezone.now()
        interval = 2
        points = []
        for i in range(150):
            base = 24 + 14 * math.sin(i / 9.0)
            points.append(
                SystemMetric(
                    cpu=max(2.0, min(96.0, base + rnd.uniform(-7, 9))),
                    ram=max(20.0, min(92.0, 58 + 9 * math.sin(i / 17.0) + rnd.uniform(-3, 4))),
                    disk=63.4,
                    gpu=None,
                    load_avg=round(0.8 + rnd.uniform(0, 0.9), 2),
                    net_sent=1_000_000 * (i + 1),
                    net_recv=4_000_000 * (i + 1),
                    running=1 if 40 <= i <= 110 else 0,
                )
            )
        created = SystemMetric.objects.bulk_create(points)
        # backdate: auto_now_add проставил «сейчас», разносим точки по времени
        for idx, obj in enumerate(created):
            ts = now - timedelta(seconds=interval * (len(created) - idx))
            SystemMetric.objects.filter(pk=obj.pk).update(created_at=ts)
        self.stdout.write(f"метрики: предзаполнено {len(created)} точек")

    def _ensure_tasks(self):
        from core.models import Task, TaskLog

        if Task.objects.exists():
            return

        admin = User.objects.get(username="admin")
        now = timezone.now()

        def add_logs(task, lines, start):
            """lines: (смещение в сек, уровень, текст)."""
            objs = [TaskLog(task=task, level=lvl, text=txt) for _, lvl, txt in lines]
            created = TaskLog.objects.bulk_create(objs)
            for (offset, _, _), obj in zip(lines, created):
                TaskLog.objects.filter(pk=obj.pk).update(created_at=start + timedelta(seconds=offset))

        # 1) завершённая задача с реальными файлами результатов
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
            finished_at=now - timedelta(hours=2),
        )
        Task.objects.filter(pk=t1.pk).update(created_at=now - timedelta(hours=2, minutes=9))
        folder = t1.result_folder()
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "транскрипт.txt"), "w", encoding="utf-8") as f:
            f.write("[00:00] Спикер 1: Мы провели четырнадцать глубинных интервью за последние две недели.\n")
            f.write("[00:07] Спикер 2: Основная проблема была в том, что пользователи не понимали, с чего начать.\n")
            f.write("[00:14] Спикер 1: Смотри, метрики удержания выросли на девять процентов после редизайна.\n")
        with open(os.path.join(folder, "сводка.json"), "w", encoding="utf-8") as f:
            f.write('{"task_id": %d, "words": 4310, "confidence": 96.4, "speakers": 2}\n' % t1.pk)
        start = now - timedelta(hours=2, minutes=9)
        add_logs(
            t1,
            [
                (0, "info", "$ python scripts/1.py --input media/uploads/demo_интервью_о_продукте.wav --output media/results/task_%d" % t1.pk),
                (2, "info", "[ffmpeg] извлечение аудиодорожки: 44 100 Гц, stereo → mono 16 кГц"),
                (5, "info", "[vad] детекция речи: Silero VAD, порог 0.35"),
                (12, "info", "[chunk] обработан фрагмент #12 из 85 (14%)"),
                (60, "info", "[chunk] обработан фрагмент #40 из 85 (47%)"),
                (180, "info", "[chunk] обработан фрагмент #71 из 85 (84%)"),
                (320, "ok", "[export] слов распознано: 4 310 · CER 2.1%"),
                (322, "ok", "[done] процесс завершён с кодом 0 · файлов в результатах: 2"),
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
            error="CUDA out of memory: не удалось выделить 6.2 ГиБ (свободно 3.1 ГиБ).",
        )
        Task.objects.filter(pk=t2.pk).update(created_at=now - timedelta(hours=5))
        add_logs(
            t2,
            [
                (0, "info", "$ python scripts/1.py --input media/uploads/demo_вебинар.mp3 --output media/results/task_%d" % t2.pk),
                (8, "info", "[chunk] обработан фрагмент #30 из 48 (63%)"),
                (14, "warn", "[gpu] VRAM занято 21.9 / 22.4 ГБ · утилизация 100%"),
                (16, "err", "RuntimeError: CUDA out of memory: tried to allocate 6.20 GiB"),
                (16, "err", "[exit] процесс завершился с кодом 1"),
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

        self.stdout.write("задачи: создано 3 демо-задачи")
