# wangumi_app/services/season_sync_service.py
from datetime import datetime
from django.db import transaction
from wangumi_app.models import Anime, SyncLog

# 如果你打算复用 scripts/download_to_psql.py 里的逻辑，可以在这里 import
# from scripts.download_to_psql import fetch_current_season_anime  # 示例

def get_current_season_year_and_quarter():
    """根据当前日期推算季度，例如 1-3 春, 4-6 夏, 7-9 秋, 10-12 冬"""
    now = datetime.now()
    year = now.year
    month = now.month
    if month in (1, 2, 3):
        quarter = "spring"
    elif month in (4, 5, 6):
        quarter = "summer"
    elif month in (7, 8, 9):
        quarter = "autumn"
    else:
        quarter = "winter"
    return year, quarter


def fetch_raw_season_data():
    """
    这里是一个抽象层：从外部数据源拿当前季度番的列表。
    你可以：
      1）直接在这里调用 download_to_psql 里的函数
      2）或者用 requests 去访问外部 API
    暂时先写个 TODO，保证结构完整，后面再填细节。
    """
    # TODO: 替换为真实数据源
    # 这里用假数据占位，结构大致是这样：
    return [
        {
            "title": "示例番剧 1",
            "status": "on_air",
            "total_episodes": 12,
            "cover_url": "",
            # ... 你们项目需要的其他字段
        },
    ]


@transaction.atomic
def sync_current_season_anime():
    """
    主同步函数：
    - 计算当前季度
    - 从外部拿数据
    - upsert 到 Anime
    - 记录 SyncLog
    """
    log = SyncLog.objects.create(
        job_type=SyncLog.JobType.SEASON,
        sync_type=SyncLog.JobType.SEASON,
        status=SyncLog.Status.PENDING,
        message="开始同步季度番",
    )
    try:
        year, quarter = get_current_season_year_and_quarter()
        raw_list = fetch_raw_season_data()

        # 这里你可以选择：
        # 方案 A：先把之前季度标记清掉，再给当前数据打标
        Anime.objects.filter(season_year=year, season_quarter=quarter).update(
            is_season_featured=False
        )

        for item in raw_list:
            # 根据你们的数据结构来 upsert，
            # 示例：title 作为唯一键之一
            anime, created = Anime.objects.update_or_create(
                title=item["title"],
                defaults={
                    "status": item.get("status") or "unknown",
                    "total_episodes": item.get("total_episodes") or 0,
                    "cover_url": item.get("cover_url") or "",
                    "season_year": year,
                    "season_quarter": quarter,
                    "is_season_featured": True,
                },
            )

        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = len(raw_list)
        log.message = f"季度番同步成功，记录数：{len(raw_list)}"
    except Exception as e:
        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = f"季度番同步失败：{e!r}"
        raise
    finally:
        log.finished_at = datetime.now()
        log.save()