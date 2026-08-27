import os
import sys

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Транскрибация"

    def ready(self):
        """Запускаем фоновый сборщик метрик системы (один экземпляр на процесс).

        Под runserver Django плодит два процесса (родитель + reload-дочка) —
        сборщик нужен только в дочке, у которой RUN_MAIN=true.
        """
        if env_disabled():
            return
        is_runserver = "runserver" in sys.argv
        if is_runserver and os.environ.get("RUN_MAIN") != "true":
            return
        try:
            from . import metrics

            metrics.start_collector()
        except Exception:  # pragma: no cover — сборщик не должен ломать запуск
            pass


def env_disabled() -> bool:
    return os.environ.get("TRANSKRIB_NO_COLLECTOR", "").lower() in ("1", "true", "yes")
