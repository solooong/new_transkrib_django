"""Модели для динамического управления скриптами транскрибации."""
import os
from django.db import models
from django.conf import settings


def script_upload_path(instance, filename):
    """
    Сохраняем скрипты в директорию, заданную в settings.TRANSCRIBE_SCRIPT_DIR.
    Это позволяет хранить все скрипты в одном месте (volume ./scripts).
    """
    return os.path.join(settings.TRANSCRIBE_SCRIPT_DIR, filename)


class ProcessingScript(models.Model):
    """
    Модель для хранения скриптов транскрибации.
    Позволяет админу загружать новые скрипты "на лету" без перезапуска контейнера.
    """
    name = models.CharField(
        "Название скрипта",
        max_length=100,
        help_text="Например: 'Whisper Large V3', 'Whisper Medium', 'Fast Model'"
    )
    file = models.FileField(
        "Файл скрипта (.py)",
        upload_to=script_upload_path,
        help_text="Python-скрипт для транскрибации (должен быть исполняемым)"
    )
    description = models.TextField(
        "Описание",
        blank=True,
        help_text="Описание модели, параметры, особенности использования"
    )
    model_name = models.CharField(
        "Название модели",
        max_length=100,
        blank=True,
        help_text="Например: 'whisper-large-v3', 'whisper-medium'"
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
        help_text="Неактивные скрипты не будут доступны для выбора"
    )
    is_default = models.BooleanField(
        "Скрипт по умолчанию",
        default=False,
        help_text="Использовать этот скрипт, если пользователь не выбрал явно"
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Скрипт транскрибации"
        verbose_name_plural = "Скрипты транскрибации"
        ordering = ["-is_default", "-is_active", "name"]

    def __str__(self):
        status = "✓" if self.is_active else "✗"
        default = " [по умолчанию]" if self.is_default else ""
        return f"{status} {self.name}{default}"

    def get_absolute_path(self):
        """Возвращает абсолютный путь к скрипту на файловой системе."""
        return os.path.join(settings.BASE_DIR, self.file.name)

    def save(self, *args, **kwargs):
        """
        При сохранении делаем этот скрипт единственным "по умолчанию",
        если он помечен как таковой.
        """
        if self.is_default:
            # Снимаем флаг is_default со всех других скриптов
            ProcessingScript.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default_script(cls):
        """Возвращает скрипт по умолчанию или None."""
        return cls.objects.filter(is_active=True, is_default=True).first()

    @classmethod
    def get_active_scripts(cls):
        """Возвращает все активные скрипты."""
        return cls.objects.filter(is_active=True)
