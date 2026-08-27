"""Фоновый сборщик метрик системы (psutil) + опциональный GPU через pynvml."""
import logging
import threading
import time

import psutil
from django.conf import settings

logger = logging.getLogger("core.metrics")

_started = False
_lock = threading.Lock()


def _gpu_percent():
    """Утилизация GPU, если установлен pynvml и доступна видеокарта NVIDIA."""
    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        pynvml.nvmlShutdown()
        return float(util)
    except Exception:
        return None


def collect() -> "SystemMetric":  # noqa: F821
    """Снимок текущих метрик (экземпляр модели, не сохранён)."""
    from .models import SystemMetric, Task

    vm = psutil.virtual_memory()
    du = psutil.disk_usage("/")
    net = psutil.net_io_counters()
    try:
        import os as _os

        load1 = float(_os.getloadavg()[0])
    except Exception:
        load1 = 0.0

    running = Task.objects.filter(status=Task.Status.RUNNING).count()

    return SystemMetric(
        cpu=psutil.cpu_percent(interval=None),
        ram=vm.percent,
        disk=du.percent,
        gpu=_gpu_percent(),
        load_avg=round(load1, 2),
        net_sent=net.bytes_sent,
        net_recv=net.bytes_recv,
        running=running,
    )


def _loop() -> None:
    """Цикл сборщика: замер -> запись в БД -> обрезка истории."""
    from django.db import connections

    from .models import SystemMetric

    interval = float(getattr(settings, "METRICS_INTERVAL", 2))
    psutil.cpu_percent(interval=None)  # первый вызов «разогревает» счётчик

    while True:
        try:
            snapshot = collect()
            snapshot.save()
            SystemMetric.prune()
        except Exception as exc:  # pragma: no cover — сборщик должен жить вечно
            logger.warning("metrics tick failed: %s", exc)
        finally:
            connections.close_all()  # не держим sqlite-соединение в потоке
        time.sleep(interval)


def start_collector() -> None:
    """Запускает единственный фоновый поток сборщика."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
        thread = threading.Thread(target=_loop, name="metrics-collector", daemon=True)
        thread.start()
        logger.info("metrics collector started (interval=%ss)", settings.METRICS_INTERVAL)
