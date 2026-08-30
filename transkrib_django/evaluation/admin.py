from django.contrib import admin

"""Админка для заданий оценки звонков."""
from django.contrib import admin

from .models import EvaluationJob


@admin.register(EvaluationJob)
class EvaluationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "user", "status", "progress", "files_total", "files_processed", "created_at")
    list_filter = ("source", "status", "created_at")
    search_fields = ("user__username", "input_folder", "output_folder")
    readonly_fields = ("created_at", "updated_at", "started_at", "finished_at", "script_path", "default_input_folder", "default_output_folder")
    
    fieldsets = (
        ("Основное", {
            "fields": ("user", "source", "script_name", "script_path")
        }),
        ("Параметры оценки", {
            "fields": ("date_from", "date_to", "input_folder", "output_folder", "default_input_folder", "default_output_folder")
        }),
        ("Опции запуска", {
            "fields": ("rebuild_excel_only", "eval_only")
        }),
        ("Статус", {
            "fields": ("status", "progress", "files_total", "files_processed", "files_failed", "error"),
            "classes": ("collapse",)
        }),
        ("Временные метки", {
            "fields": ("created_at", "updated_at", "started_at", "finished_at"),
            "classes": ("collapse",)
        }),
    )
