import logging
from typing import Optional

from django.contrib.sessions.models import Session
from django.utils import timezone

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    from rest_framework_simplejwt.token_blacklist.models import (
        BlacklistedToken,
        OutstandingToken,
    )
except Exception:  # pragma: no cover - handled gracefully at runtime
    BlacklistedToken = None  # type: ignore
    OutstandingToken = None  # type: ignore


def invalidate_user_sessions_and_tokens(user) -> None:
    """Remove active sessions and blacklist refresh tokens for the given user."""
    if user is None:
        return
    _invalidate_sessions(user)
    _blacklist_tokens(user)


def _invalidate_sessions(user) -> None:
    try:
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        user_id = str(user.pk)
        for session in active_sessions:
            data = session.get_decoded()
            if data.get("_auth_user_id") == user_id:
                session.delete()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to invalidate sessions for user %s: %s", user.pk, exc)


def _blacklist_tokens(user) -> None:
    if OutstandingToken is None or BlacklistedToken is None:
        return
    try:
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning("Failed to blacklist tokens for user %s: %s", user.pk, exc)
