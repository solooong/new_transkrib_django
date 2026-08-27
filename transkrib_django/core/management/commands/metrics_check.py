"""Self-test сборщика метрик: один замер, сохранение, вывод таблицы.

    docker compose exec web python manage.py metrics_check
"""
from django.core.management.base import BaseCommand

from core.metrics import snapshot_and_save
from core.models import SystemMetric


class Command(BaseCommand):
    help = "Разовый замер системных метрик (тест мониторинга)"

    def handle(self, *args, **options):
        self.stdout.write("Снимаем метрики…")
        point = snapshot_and_save()
        SystemMetric.prune()

        rows = [
            ("CPU", f"{point.cpu:.1f}%"),
            ("RAM", f"{point.ram:.1f}%"),
            ("Диск", f"{point.disk:.1f}%"),
            ("GPU", "н/д" if point.gpu is None else f"{point.gpu:.0f}%"),
            ("Load avg", f"{point.load_avg:.2f}"),
            ("Сеть ↑", f"{point.net_sent / 1048576:.1f} МБ"),
            ("Сеть ↓", f"{point.net_recv / 1048576:.1f} МБ"),
            ("Активных задач", str(point.running)),
        ]

        width = max(len(k) for k, _ in rows)
        for key, value in rows:
            self.stdout.write(f"  {key.ljust(width)} : {value}")

        total = SystemMetric.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"\nТочка сохранена (id={point.pk}). Всего точек в истории: {total}. "
                "Дашборд подхватит её автоматически."
            )
        )
