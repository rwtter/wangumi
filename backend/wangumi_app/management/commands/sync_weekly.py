from typing import Any

from django.core.management.base import BaseCommand

from wangumi_app.services.weekly_sync_service import sync_weekly_collections


class Command(BaseCommand):
    help = "同步周合集数据"

    def handle(self, *args: Any, **options: Any):
        success, stats = sync_weekly_collections()
        created = stats.get("created", 0)
        updated = stats.get("updated", 0)

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    f"周合集同步成功: created={created}, updated={updated}"
                )
            )
        else:
            # 在错误场景下直接写入 stderr，避免被当成正常输出
            self.stderr.write(self.style.ERROR("周合集同步失败，请查看日志"))
