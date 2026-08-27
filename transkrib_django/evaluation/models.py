from django.db import models

"""Модели для оценки звонков - оценка транскрипций и отчёты."""
import os
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class EvaluationJob(models.Model):
    """Задание оценки транскрипций (ГазОйл, Евроойл, КоллЦентр)."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "В очереди"
        RUNNING = "running", "Выполняется"
        DONE = "done", "Завершено"
        ERROR = "error", "Ошибка"
    
    class SourceType(models.TextChoices):
        GAZOIL = "gazoil", "ГазОйл"
        EUROOIL = "eurooil", "Евроойл"
        CALLCENTRE = "callcentre", "КоллЦентр"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluation_jobs", verbose_name="Пользователь")
    source = models.CharField("Источник", max_length=32, choices=SourceType.choices)
    
    # Параметры оценки
    date_from = models.DateField("Дата с", null=True, blank=True)
    date_to = models.DateField("Дата по", null=True, blank=True)
    input_folder = models.CharField("Папка с аудио", max_length=512, blank=True, default="")
    output_folder = models.CharField("Папка результатов", max_length=512, blank=True, default="")
    
    # Опции запуска
    rebuild_excel_only = models.BooleanField("Только сборка Excel", default=False)
    eval_only = models.BooleanField("Только оценка", default=False)
    
    # Статус выполнения
    status = models.CharField("Статус", max_length=10, choices=Status.choices, default=Status.PENDING)
    progress = models.PositiveSmallIntegerField("Прогресс, %", default=0)
    files_total = models.PositiveIntegerField("Всего файлов", default=0)
    files_processed = models.PositiveIntegerField("Обработано", default=0)
    files_failed = models.PositiveIntegerField("Ошибок", default=0)
    error = models.TextField("Ошибка", blank=True)
    
    # Скрипт
    script_name = models.CharField("Скрипт", max_length=256, default="")
    
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    started_at = models.DateTimeField("Начато", null=True, blank=True)
    finished_at = models.DateTimeField("Завершено", null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Задание оценки"
        verbose_name_plural = "Задания оценки"
    
    def __str__(self):
        return f"Evaluation #{self.pk} — {self.get_source_display()}"
    
    @property
    def script_path(self) -> str:
        """Полный путь к скрипту оценки."""
        if not self.script_name:
            mapping = {
                self.SourceType.GAZOIL: "final_report_gazoil.py",
                self.SourceType.EUROOIL: "final_report_eurooil.py",
                self.SourceType.CALLCENTRE: "final_report_callcentre.py",
            }
            self.script_name = mapping.get(self.source, "")
            self.save(update_fields=["script_name"])
        return os.path.join(settings.BASE_DIR, "scripts", self.script_name)
    
    @property
    def default_input_folder(self) -> str:
        """Папка входных данных по умолчанию."""
        return os.path.join(settings.MEDIA_ROOT, "imports", self.source)
    
    @property
    def default_output_folder(self) -> str:
        """Папка результатов по умолчанию."""
        return os.path.join(settings.MEDIA_ROOT, "evaluations", self.source, timezone.now().strftime("%Y-%m-%d"))
    
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
            "files_total": self.files_total,
            "files_processed": self.files_processed,
            "files_failed": self.files_failed,
            "created": self.created_at.strftime("%d.%m %H:%M"),
        }
