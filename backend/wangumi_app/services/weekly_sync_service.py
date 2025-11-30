# backend/wangumi_app/services/weekly_sync_service.py

from __future__ import annotations
import logging
from typing import Dict, Any, Tuple, List

from django.utils.dateparse import parse_date

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
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("周合集接口返回格式错误，预期为 JSON 对象")
    return data


def _normalize_item(item: Dict[str, Any], collection: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    external_id = item.get("external_id") or item.get("id")
    if not external_id:
        raise ValueError(f"缺少 external_id 字段: {item}")

    title = item.get("title") or item.get("name") or item.get("name_cn") or "未命名番剧"
    title_cn = item.get("title_cn") or item.get("name_cn") or title

    cover = item.get("cover") or item.get("image") or collection.get("cover") or ""
    platform = item.get("platform") or collection.get("platform") or ""

    release_date_str = item.get("release_date")
    release_date = parse_date(release_date_str) if release_date_str else None

    defaults = {
        "title": title,
        "title_cn": title_cn,
        "cover_url": cover or "",
        "platform": platform,
        "genres": item.get("genres") or [],
        "airtime": item.get("airtime") or "",
        "total_episodes": item.get("total_episodes") or item.get("episodes") or 0,
        "is_weekly_featured": True,
    }

    if release_date:
        defaults["release_date"] = release_date

    return str(external_id), defaults


def _iter_items(collections: List[Dict[str, Any]]):
    for collection in collections:
        items = collection.get("items") or collection.get("anime_list") or []
        for raw_item in items:
            yield collection, raw_item


def sync_weekly_collections() -> Tuple[bool, Dict[str, Any]]:
    """
    周合集同步：调用外部 API → 创建/更新 Anime → 写日志
    返回 (成功与否, 统计信息)
    """
    log: SyncLog | None = None
    created, updated = 0, 0

    try:
        log = SyncLog.objects.create(
            job_type=SyncLog.JobType.WEEKLY,
            sync_type=SyncLog.JobType.WEEKLY,
            status=SyncLog.Status.PENDING,
            message="开始同步周合集",
        )

        payload = fetch_weekly_data()
        collections = payload.get("collections", [])

        for collection, raw_item in _iter_items(collections):
            try:
                external_id, defaults = _normalize_item(raw_item, collection)
            except Exception as exc:  # pragma: no cover - logged below
                logger.exception("跳过无效条目", extra={"item": raw_item, "reason": str(exc)})
                continue

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
        log.message = f"周合集同步完成: created={created}, updated={updated}"
    except Exception as exc:
        if log is None:
            # 如果日志模型创建都失败了，只能向外抛异常让调用方处理
            logger.exception("初始化同步日志失败")
            raise

        log.status = SyncLog.Status.FAILURE
        log.success = False
        log.message = str(exc)
        logger.exception("周合集同步失败")
    finally:
        if log is not None:
            log.finished_at = timezone.now()
            log.save()

    # log 不会为 None，前面抛出异常也会冒泡
    return log.status == SyncLog.Status.SUCCESS, {"log_id": log.id, "created": created, "updated": updated}
