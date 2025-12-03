import hashlib
import logging
from datetime import timedelta
from typing import Iterable, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when a caller exceeds the configured verification code limits."""


def enforce_verification_code_rate_limits(
    identifier: str,
    purpose: str,
    requester_ip: Optional[str],
) -> None:
    """
    Apply per-identifier and per-IP throttling for verification code requests.
    """
    now = timezone.now()
    min_interval = max(int(getattr(settings, "VERIFICATION_CODE_REQUEST_INTERVAL_SECONDS", 60)), 0)
    daily_target_limit = int(getattr(settings, "VERIFICATION_CODE_DAILY_LIMIT_PER_TARGET", 10))
    daily_ip_limit = int(getattr(settings, "VERIFICATION_CODE_DAILY_LIMIT_PER_IP", 50))

    normalized_identifier = (identifier or "").strip().lower()
    normalized_purpose = (purpose or "").strip().lower()
    ip_value = (requester_ip or "").strip()

    if normalized_identifier:
        interval_key = f"{normalized_purpose}:{normalized_identifier}"
        _enforce_interval(("target", interval_key), min_interval, now)
        _enforce_daily(("target", interval_key), daily_target_limit, now)

    if ip_value:
        interval_key = f"{normalized_purpose}:{ip_value}"
        _enforce_interval(("ip", interval_key), min_interval, now)
        _enforce_daily(("ip", interval_key), daily_ip_limit, now)


def _enforce_interval(parts: Iterable[str], interval_seconds: int, now) -> None:
    if interval_seconds <= 0:
        return
    key = _build_cache_key(("interval", *parts))
    if cache.get(key):
        raise RateLimitError("请求过于频繁，请稍后再试")
    cache.set(key, now.isoformat(), interval_seconds)


def _enforce_daily(parts: Iterable[str], daily_limit: int, now) -> None:
    if daily_limit <= 0:
        return
    date_suffix = now.strftime("%Y%m%d")
    key = _build_cache_key(("daily", *parts, date_suffix))
    current = cache.get(key, 0)
    if current >= daily_limit:
        raise RateLimitError("验证码请求已超过当日上限")
    ttl = max(1, int(_seconds_until_day_end(now)))
    cache.set(key, current + 1, ttl)


def _seconds_until_day_end(now) -> float:
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    delta = tomorrow - now
    return max(delta.total_seconds(), 0.0)


def _build_cache_key(parts: Iterable[str]) -> str:
    raw = ":".join(str(part) for part in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    prefix = getattr(settings, "SMS_RATE_LIMIT_CACHE_PREFIX", "verification_rate")
    return f"{prefix}:{digest}"


__all__ = ["RateLimitError", "enforce_verification_code_rate_limits"]
