# backend/wangumi_app/services/weekly_sync_service.py

from __future__ import annotations
import logging
from typing import Dict, Any, Tuple

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from wangumi_app.models import Anime, SyncLog

logger = logging.getLogger(__name__)


def fetch_weekly_data() -> Dict[str, Any]:
    """从外部 API 获取周合集数据"""
    resp = requests.get(settings.WEEKLY_COLLECTION_API, timeout=10)
    resp.raise_for_status()
    return resp.json()


def sync_weekly_collections() -> Tuple[bool, Dict[str, Any]]:
    """
    周合集同步：调用外部 API → 创建/更新 Anime → 写日志
    返回 (成功与否, 统计信息)
    """
    log = SyncLog.objects.create(job_type=SyncLog.JobType.WEEKLY)
    created, updated = 0, 0

    try:
        payload = fetch_weekly_data()
        collections = payload.get("collections", [])  # 按实际 API 结构改

        for col in collections:
            for item in col.get("anime_list", []):
                anime, is_created = Anime.objects.update_or_create(
                    external_id=item["id"],  # 按实际字段修改
                    defaults={
                        "title": item["title"],
                        "cover_url": item.get("cover"),
                        # …你自己的字段…
                    },
                )
                created += is_created
                updated += (not is_created)

        log.status = SyncLog.Status.SUCCESS
        log.created_count = created
        log.updated_count = updated
        log.message = f"周合集同步完成: created={created}, updated={updated}"
    except Exception as exc:
        log.status = SyncLog.Status.FAIL
        log.message = str(exc)
        logger.exception("周合集同步失败")

    log.finished_at = timezone.now()
    log.save()
    return log.status == SyncLog.Status.SUCCESS, {"log_id": log.id, "created": created, "updated": updated}
