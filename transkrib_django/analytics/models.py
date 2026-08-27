from django.db import models

"""Модели для аналитики звонков - импорт аудио из различных источников."""
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class ImportJob(models.Model):
    """Задание импорта аудио из внешних источников (АТС ГазОйл, Евроойл, КоллЦентр)."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "В очереди"
        RUNNING = "running", "Выполняется"
        DONE = "done", "Завершено"
        ERROR = "error", "Ошибка"
    
    class SourceType(models.TextChoices):
        GAZOIL = "gazoil", "ГазОйл"
        EUROOIL = "eurooil", "Евроойл"
        CALLCENTRE = "callcentre", "КоллЦентр"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="import_jobs", verbose_name="Пользователь")
    source = models.CharField("Источник", max_length=32, choices=SourceType.choices)
    
    # Параметры импорта
    date_from = models.DateField("Дата с", null=True, blank=True)
    date_to = models.DateField("Дата по", null=True, blank=True)
    phone_filter = models.CharField("Фильтр по телефону", max_length=64, blank=True, default="")
    department_filter = models.CharField("Фильтр по отделу", max_length=128, blank=True, default="")
    
    # Настройки
    skip_existing = models.BooleanField("Пропускать существующие", default=True)
    min_duration_sec = models.IntegerField("Мин. длительность (сек)", default=0)
    output_folder = models.CharField("Папка назначения", max_length=512, blank=True, default="")
    
    # Статус выполнения
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.PENDING)
    progress = models.PositiveSmallIntegerField("Прогресс, %", default=0)
    records_found = models.PositiveIntegerField("Найдено записей", default=0)
    records_imported = models.PositiveIntegerField("Импортировано", default=0)
    records_skipped = models.PositiveIntegerField("Пропущено", default=0)
    records_failed = models.PositiveIntegerField("Ошибок", default=0)
    error = models.TextField("Ошибка", blank=True)
    
    # Скрипт
    script_name = models.CharField("Скрипт", max_length=256, default="")
    
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    started_at = models.DateTimeField("Начато", null=True, blank=True)
    finished_at = models.DateTimeField("Завершено", null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Задание импорта"
        verbose_name_plural = "Задания импорта"
    
    def __str__(self):
        return f"Import #{self.pk} — {self.get_source_display()}"
    
    @property
    def script_path(self) -> str:
        """Полный путь к скрипту импорта."""
        if not self.script_name:
            mapping = {
                self.SourceType.GAZOIL: "import_from_ats_gazoil.py",
                self.SourceType.EUROOIL: "import_from_ats_eurooil.py",
                self.SourceType.CALLCENTRE: "import_from_ats_callcentre.py",
            }
            self.script_name = mapping.get(self.source, "")
            self.save(update_fields=["script_name"])
        return os.path.join(settings.BASE_DIR, "scripts", self.script_name)
    
    @property
    def default_output_folder(self) -> str:
        """Папка по умолчанию для сохранения импортированных файлов."""
        return os.path.join(settings.MEDIA_ROOT, "imports", self.source, timezone.now().strftime("%Y-%m-%d"))
    
    def to_api(self) -> dict:
        """Сериализация для API."""
        return {
            "id": self.pk,
            "source": self.source,
            "source_label": self.get_source_display(),
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "status": self.status,
            "status_label": self.get_status_display(),
            "progress": self.progress,
            "records_found": self.records_found,
            "records_imported": self.records_imported,
            "records_skipped": self.records_skipped,
            "records_failed": self.records_failed,
            "created": self.created_at.strftime("%d.%m %H:%M"),
        }
