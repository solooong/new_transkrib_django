"""Админка Django с ролевой моделью и управлением скриптами."""
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Task, TaskLog
from .models_scripts import ProcessingScript


# =============================================================================
# Ролевая модель: настройка групп и прав доступа
# =============================================================================

def setup_groups():
    """Создаёт группы пользователей с правами доступа."""
    try:
        # Группа "Клиенты" - видят только свои задачи
        clients_group, created = Group.objects.get_or_create(name="Клиенты")
        if created:
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            task_ct = ContentType.objects.get_for_model(Task)
            view_perm = Permission.objects.get(content_type=task_ct, codename="view_task")
            clients_group.permissions.add(view_perm)
        
        # Группа "Операторы" - видят все задачи, могут управлять скриптами
        operators_group, created = Group.objects.get_or_create(name="Операторы")
        if created:
            from django.contrib.auth.models import Permission
            from django.contrib.contenttypes.models import ContentType
            
            task_ct = ContentType.objects.get_for_model(Task)
            task_log_ct = ContentType.objects.get_for_model(TaskLog)
            
            task_perms = Permission.objects.filter(content_type=task_ct)
            task_log_perms = Permission.objects.filter(content_type=task_log_ct)
            
            operators_group.permissions.add(*task_perms, *task_log_perms)
    except Exception:
        pass  # Игнорируем ошибки при миграциях


# Вызываем при загрузке модуля
try:
    setup_groups()
except Exception:
    pass


# =============================================================================
# Админка для ProcessingScript
# =============================================================================

@admin.register(ProcessingScript)
class ProcessingScriptAdmin(admin.ModelAdmin):
    """Управление скриптами транскрибации.
    
    Доступно только суперпользователям и операторам.
    """
    list_display = ("name", "model_name", "is_active", "is_default", "created_at")
    list_filter = ("is_active", "is_default")
    search_fields = ("name", "description", "model_name")
    list_editable = ("is_active", "is_default")
    
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "file", "description")
        }),
        ("Настройки", {
            "fields": ("model_name", "is_active", "is_default")
        }),
    )
    
    # Скрипты видят только суперпользователи и операторы
    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.groups.filter(name="Операторы").exists()
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.groups.filter(name="Операторы").exists()
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.groups.filter(name="Операторы").exists()


# =============================================================================
# Админка для Task с фильтрацией по пользователю
# =============================================================================

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
    """Управление задачами транскрибации.
    
    Клиенты видят только свои задачи.
    Операторы и суперпользователи видят все задачи.
    """
    list_display = ("id", "display_name", "user", "script", "status", "progress", "model", "words", "created_at")
    list_filter = ("status", "model", "language", "script")
    search_fields = ("original_name", "user__username", "transcript_text")
    readonly_fields = ("created_at", "updated_at", "finished_at")
    inlines = (TaskLogInline,)
    
    fieldsets = (
        ("Файл", {"fields": ("input_file", "original_name", "size_bytes", "duration_sec")}),
        ("Параметры транскрибации", {
            "fields": ("script", "language", "model", "diarization", "diarization_method", 
                      "timeout_sec", "gpu_id", "metadata_json", "output_path")
        }),
        ("Статус", {"fields": ("status", "progress", "error", "created_at", "updated_at", "finished_at")}),
    )
    
    # Фильтрация задач по пользователю
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Клиенты видят только свои задачи
        if request.user.groups.filter(name="Клиенты").exists():
            return qs.filter(user=request.user)
        # Операторы видят все задачи
        if request.user.groups.filter(name="Операторы").exists():
            return qs
        return qs.filter(user=request.user)
    
    # Поле script доступно только операторам и суперпользователям
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not (request.user.is_superuser or request.user.groups.filter(name="Операторы").exists()):
            # Убираем поле script для клиентов
            for name, options in fieldsets:
                if "fields" in options:
                    options["fields"] = [f for f in options["fields"] if f != "script"]
        return fieldsets


# =============================================================================
# Админка для TaskLog
# =============================================================================

@admin.register(TaskLog)
class TaskLogAdmin(admin.ModelAdmin):
    """Просмотр журналов задач.
    
    Доступно только операторам и суперпользователям.
    """
    list_display = ("id", "task", "level", "short_text", "created_at")
    list_filter = ("level",)

    @admin.display(description="Текст")
    def short_text(self, obj):
        return obj.text[:80]
    
    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.groups.filter(name="Операторы").exists()


# =============================================================================
# Кастомная админка для User с группами
# =============================================================================

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Управление пользователями с отображением групп."""
    list_display = ("username", "email", "is_staff", "is_active", "get_groups")
    list_filter = ("is_staff", "is_active", "groups")
    
    @admin.display(description="Группы")
    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
