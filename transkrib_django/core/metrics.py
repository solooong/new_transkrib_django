"""Фоновый сборщик метрик системы (psutil) + опциональный GPU через pynvml.

Сборщик:
  * стартует один раз на процесс (см. apps.py);
  * каждые METRICS_INTERVAL секунд пишет точку SystemMetric;
  * история обрезается до METRICS_KEEP точек;
  * NVML (NVIDIA) инициализируется один раз и переиспользуется.
"""
import logging
import threading
import time

import psutil
from django.conf import settings

logger = logging.getLogger("core.metrics")

_started = False
_lock = threading.Lock()

# Кэш NVML: состояния "unknown" -> "on" / "off" (off — больше не пробуем).
_nvml = {"state": "unknown", "handle": None}


def _gpu_percent():
    """Утилизация GPU 0-й видеокарты NVIDIA, None если GPU недоступен."""
    if _nvml["state"] == "off":
        return None
    try:
        import pynvml

        if _nvml["state"] == "unknown":
            pynvml.nvmlInit()
            _nvml["handle"] = pynvml.nvmlDeviceGetHandleByIndex(0)
            _nvml["state"] = "on"
            logger.info("pynvml: GPU обнаружен")
        util = pynvml.nvmlDeviceGetUtilizationRates(_nvml["handle"]).gpu
        return float(util)
    except Exception:
        if _nvml["state"] == "unknown":
            logger.info("pynvml: GPU недоступен, метрика gpu отключена")
        _nvml["state"] = "off"
        return None


def collect() -> "SystemMetric":  # noqa: F821
    """Снимок текущих метрик (экземпляр модели, НЕ сохранён в БД)."""
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


def snapshot_and_save() -> "SystemMetric":  # noqa: F821
    """Сделать один замер и сразу сохранить его. Используется и сборщиком, и self-test."""
    point = collect()
    point.save()
    return point


def _loop() -> None:
    """Цикл сборщика: замер -> запись в БД -> обрезка истории."""
    from django.db import connections

    from .models import SystemMetric

    interval = float(getattr(settings, "METRICS_INTERVAL", 2))
    psutil.cpu_percent(interval=None)  # первый вызов «разогревает» счётчик

    while True:
        try:
            point = snapshot_and_save()
            SystemMetric.prune()
            logger.debug("metrics: cpu=%.1f ram=%.1f gpu=%s", point.cpu, point.ram, point.gpu)
        except Exception as exc:  # pragma: no cover — сборщик должен жить вечно
            logger.warning("metrics tick failed: %s", exc)
        finally:
            connections.close_all()  # не держим sqlite-соединение в потоке
        time.sleep(interval)


def start_collector() -> None:
    """Запускает единственный фоновый поток сборщика (идемпотентно)."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
        thread = threading.Thread(target=_loop, name="metrics-collector", daemon=True)
        thread.start()
        logger.info("metrics collector started (interval=%ss)", settings.METRICS_INTERVAL)
