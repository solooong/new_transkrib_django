from django.contrib import admin

"""Админка для заданий импорта аудио."""
from django.contrib import admin

from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "user", "status", "progress", "records_found", "records_imported", "created_at")
    list_filter = ("source", "status", "created_at")
    search_fields = ("user__username", "phone_filter", "department_filter")
    readonly_fields = ("created_at", "updated_at", "started_at", "finished_at", "script_path", "default_output_folder")
    
    fieldsets = (
        ("Основное", {
            "fields": ("user", "source", "script_name", "script_path")
        }),
        ("Параметры импорта", {
            "fields": ("date_from", "date_to", "phone_filter", "department_filter")
        }),
        ("Настройки", {
            "fields": ("skip_existing", "min_duration_sec", "output_folder", "default_output_folder")
        }),
        ("Статус", {
            "fields": ("status", "progress", "records_found", "records_imported", "records_skipped", "records_failed", "error"),
            "classes": ("collapse",)
        }),
        ("Временные метки", {
            "fields": ("created_at", "updated_at", "started_at", "finished_at"),
            "classes": ("collapse",)
        }),
    )
