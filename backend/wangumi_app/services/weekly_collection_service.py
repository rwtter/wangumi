# wangumi_app/services/weekly_collection_service.py
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from wangumi_app.models import Anime, SyncLog

@transaction.atomic
def generate_weekly_collection():
    """
    这里的“周合集”逻辑你们组可以自己定：
      - 比如选最近 7 天内更新的动画，
      - 或者选当前季度中评分最高/热度最高的前 N 个，
      - 暂时先用简单规则代替，保证逻辑闭环。
    """
    log = SyncLog.objects.create(
        job_type=SyncLog.JobType.WEEKLY,
        sync_type=SyncLog.JobType.WEEKLY,
        status=SyncLog.Status.PENDING,
        message="开始生成周合集",
    )
    try:
        now = timezone.now()

        # 示例：把当前季度的推荐番全部标记为 weekly（真实逻辑你们可以细化）
        qs = Anime.objects.filter(is_season_featured=True)
        # 先清除旧的 weekly 标志
        Anime.objects.filter(is_weekly_featured=True).update(is_weekly_featured=False)
        # 再把本次选中的打标
        qs.update(is_weekly_featured=True)

        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = qs.count()
        log.message = f"周合集生成成功，本周推荐番数量：{qs.count()}"
    except Exception as e:
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = f"周合集生成失败：{e!r}"
        raise
    finally:
        log.finished_at = datetime.now()
        log.save()
