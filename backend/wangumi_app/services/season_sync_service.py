"""季度番同步服务"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings
from django.db import transaction
from django.utils.dateparse import parse_date

from wangumi_app.models import Anime, SyncLog

logger = logging.getLogger(__name__)

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


def fetch_raw_season_data() -> List[Dict[str, Any]]:
    """
    从外部接口拉取当前季度番数据。

    期待 API 返回数组，每个元素包含至少 `external_id` 或 `id` 以及标题、封面等字段。
    """
    resp = requests.get(settings.SEASON_COLLECTION_API, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise ValueError("季度番接口返回格式错误，预期为 JSON 数组")
    return data


def _normalize_item(item: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    external_id = item.get("external_id") or item.get("id")
    if not external_id:
        raise ValueError(f"缺少 external_id 字段: {item}")

    title = item.get("title") or item.get("name") or "未命名番剧"
    title_cn = item.get("title_cn") or item.get("name_cn") or title
    cover = item.get("cover") or item.get("image") or item.get("cover_url") or ""

    release_date_str = item.get("release_date")
    release_date = parse_date(release_date_str) if release_date_str else None

    defaults: Dict[str, Any] = {
        "title": title,
        "title_cn": title_cn,
        "cover_url": cover,
        "status": item.get("status") or "unknown",
        "total_episodes": item.get("total_episodes") or item.get("episodes") or 0,
        "platform": item.get("platform") or "",
        "genres": item.get("genres") or [],
        "airtime": item.get("airtime") or "",
        "is_season_featured": True,
    }

    if release_date:
        defaults["release_date"] = release_date

    return str(external_id), defaults


@transaction.atomic
def sync_current_season_anime() -> Tuple[bool, Dict[str, Any]]:
    """
    主同步函数：
    - 计算当前季度
    - 从外部拿数据
    - upsert 到 Anime
    - 记录 SyncLog

    返回 (成功与否, 统计信息)
    """
    log: SyncLog | None = None
    created, updated = 0, 0

    try:
        log = SyncLog.objects.create(
            job_type=SyncLog.JobType.SEASON,
            sync_type=SyncLog.JobType.SEASON,
            status=SyncLog.Status.PENDING,
            message="开始同步季度番",
        )

        year, quarter = get_current_season_year_and_quarter()
        raw_list = fetch_raw_season_data()

        Anime.objects.filter(season_year=year, season_quarter=quarter).update(
            is_season_featured=False
        )

        for raw_item in raw_list:
            external_id, defaults = _normalize_item(raw_item)
            defaults.update({
                "season_year": year,
                "season_quarter": quarter,
            })

            anime, is_created = Anime.objects.update_or_create(
                external_id=external_id,
                defaults=defaults,
            )

            created += int(is_created)
            updated += int(not is_created)

        log.status = SyncLog.Status.SUCCESS
        log.success = True
        log.created_count = created
        log.updated_count = updated
        log.message = f"季度番同步成功: created={created}, updated={updated}"
    except Exception as exc:
        if log is None:
            logger.exception("初始化季度番同步日志失败")
            raise

        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = str(exc)
        logger.exception("季度番同步失败")
    finally:
        if log is not None:
            log.finished_at = datetime.now()
            log.save()

    return log.status == SyncLog.Status.SUCCESS, {"log_id": log.id, "created": created, "updated": updated}
