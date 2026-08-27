from django.contrib import admin

from .models import SystemMetric, Task, TaskLog


class TaskLogInline(admin.TabularInline):
    model = TaskLog
    extra = 0
    fields = ("level", "text", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-id",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "display_name", "user", "status", "progress", "model", "created_at", "finished_at")
    list_filter = ("status", "model", "language")
    search_fields = ("original_name", "user__username")
    readonly_fields = ("created_at", "updated_at", "finished_at")
    inlines = (TaskLogInline,)


@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "level", "short_text", "created_at")
    list_filter = ("level",)

    @admin.display(description="Текст")
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "cpu", "ram", "gpu", "disk", "running")
    list_filter = ("created_at",)
