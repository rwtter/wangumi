from django.core.management.base import BaseCommand

from wangumi_app.services.weekly_sync_service import sync_weekly_collections


class Command(BaseCommand):
    help = "同步周合集数据"

    def handle(self, *args, **options):
        success, stats = sync_weekly_collections()
        created = stats.get("created", 0) if stats else 0
        updated = stats.get("updated", 0) if stats else 0

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"周合集同步成功: created={created}, updated={updated}"
                )
            )
        else:
            msg = self.style.ERROR("周合同步失败，请查看日志")
            self.stdout.write(msg)
