"""Модели: задачи транскрибации, построчные журналы, метрики системы."""
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

ALLOWED_EXTENSIONS = [
    "mp3", "wav", "m4a", "ogg", "flac", "aac", "wma", "opus",
    "mp4", "mkv", "webm", "mov", "avi",
]


class Task(models.Model):
    """Задача транскрибации (аналог задачи из README, расширен)."""

    class Status(models.TextChoices):
        PENDING = "pending", "В очереди"
        RUNNING = "running", "Выполняется"
        DONE = "done", "Завершено"
        ERROR = "error", "Ошибка"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks", verbose_name="Пользователь")
    input_file = models.FileField(
        "Файл",
        upload_to="uploads/",
        validators=[FileExtensionValidator(ALLOWED_EXTENSIONS)],
    )
    original_name = models.CharField("Исходное имя", max_length=255, blank=True)
    size_bytes = models.BigIntegerField("Размер, байт", default=0)
    duration_sec = models.FloatField("Длительность, сек", null=True, blank=True)

    language = models.CharField("Язык", max_length=32, default="Русский")
    model = models.CharField("Модель", max_length=64, default="large-v3-turbo")
    diarization = models.BooleanField("Диаризация спикеров", default=True)
    
    # Новые поля для аргументов скрипта
    diarization_method = models.CharField("Метод диаризации", max_length=32, default="spectral", 
                                          choices=[("ecapa", "ecapa"), ("spectral", "spectral")])
    timeout_sec = models.IntegerField("Таймаут (мс)", default=60000)
    gpu_id = models.IntegerField("ID GPU", default=0)
    metadata_json = models.TextField("Метаданные JSON", blank=True, default="")
    output_path = models.CharField("Путь вывода", max_length=512, blank=True, default="")

    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.PENDING)
    progress = models.PositiveSmallIntegerField("Прогресс, %", default=0)
    error = models.TextField("Ошибка", blank=True)

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)
    finished_at = models.DateTimeField("Завершена", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    def __str__(self):
        return f"Task #{self.pk} — {self.display_name}"

    # ---- вычисляемые свойства --------------------------------------------
    @property
    def display_name(self) -> str:
        return self.original_name or os.path.basename(self.input_file.name or "файл")

    @property
    def size_human(self) -> str:
        mb = (self.size_bytes or 0) / 1048576
        return f"{mb / 1024:.2f} ГБ" if mb >= 1024 else f"{mb:.1f} МБ"

    @property
    def duration_human(self) -> str:
        if not self.duration_sec:
            return "—"
        total = int(self.duration_sec)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def result_folder(self) -> str:
        """Папка результатов: media/results/task_<id> (создаётся воркером)."""
        return os.path.join(settings.MEDIA_ROOT, "results", f"task_{self.pk}")

    def result_files(self):
        """Список (имя, человекочитаемый размер) файлов в папке результатов."""
        folder = self.result_folder()
        if not os.path.isdir(folder):
            return []
        items = []
        for name in sorted(os.listdir(folder)):
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            kb = os.path.getsize(path) / 1024
            size = f"{kb / 1024:.2f} МБ" if kb >= 1024 else f"{kb:.1f} КБ"
            items.append({"name": name, "size": size})
        return items

    def to_api(self) -> dict:
        """Сериализация для live-обновления таблицы на дашборде."""
        return {
            "id": self.pk,
            "file": self.display_name,
            "size": self.size_human,
            "model": self.model,
            "language": self.language,
            "duration": self.duration_human,
            "status": self.status,
            "status_label": self.get_status_display(),
            "progress": self.progress,
            "created": self.created_at.strftime("%d.%m %H:%M"),
            "url": f"/task/{self.pk}/",
            "diarization": self.diarization,
            "diarization_method": self.diarization_method,
            "timeout_sec": self.timeout_sec,
            "gpu_id": self.gpu_id,
        }


class TaskLog(models.Model):
    """Построчный журнал выполнения задачи (вместо одного TextField)."""

    class Level(models.TextChoices):
        INFO = "info", "Инфо"
        OK = "ok", "Успех"
        WARN = "warn", "Предупреждение"
        ERR = "err", "Ошибка"

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="logs", verbose_name="Задача")
    level = models.CharField("Уровень", max_length=4, choices=Level.choices, default=Level.INFO)
    text = models.TextField("Строка")
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["task", "id"])]
        verbose_name = "Строка журнала"
        verbose_name_plural = "Журналы задач"

    def __str__(self):
        return f"[{self.task_id}] {self.text[:60]}"


class SystemMetric(models.Model):
    """История метрик системы для графиков дашборда."""

    created_at = models.DateTimeField("Время", auto_now_add=True, db_index=True)
    cpu = models.FloatField("CPU, %", default=0)
    ram = models.FloatField("RAM, %", default=0)
    disk = models.FloatField("Диск, %", default=0)
    gpu = models.FloatField("GPU, %", null=True, blank=True)
    load_avg = models.FloatField("Load avg", default=0)
    net_sent = models.BigIntegerField("Сеть: отправлено, байт", default=0)
    net_recv = models.BigIntegerField("Сеть: получено, байт", default=0)
    running = models.PositiveSmallIntegerField("Активных задач", default=0)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Метрика системы"
        verbose_name_plural = "Метрики системы"

    @classmethod
    def prune(cls, keep: int | None = None) -> None:
        """Оставляем только последние `keep` точек."""
        keep = keep or getattr(settings, "METRICS_KEEP", 2160)
        excess = cls.objects.count() - keep
        if excess > 0:
            old_ids = cls.objects.order_by("id").values_list("id", flat=True)[:excess]
            cls.objects.filter(id__in=list(old_ids)).delete()

    def to_api(self) -> dict:
        return {
            "t": int(self.created_at.timestamp() * 1000),
            "cpu": round(self.cpu, 1),
            "ram": round(self.ram, 1),
            "disk": round(self.disk, 1),
            "gpu": None if self.gpu is None else round(self.gpu, 1),
            "load": round(self.load_avg, 2),
            "running": self.running,
        }


def now():
    return timezone.now()
