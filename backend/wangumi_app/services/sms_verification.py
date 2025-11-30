import hashlib
import logging
import os
import random
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.utils import timezone

from .rate_limiter import enforce_verification_code_rate_limits

try:  # pragma: no cover - optional dependency
    import redis
except ImportError:  # pragma: no cover - handled at runtime
    redis = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.sms.v20210111 import models as sms_models
    from tencentcloud.sms.v20210111.sms_client import SmsClient
except ImportError:
    credential = None
    ClientProfile = None
    HttpProfile = None
    sms_models = None
    SmsClient = None

logger = logging.getLogger(__name__)

ALLOWED_PURPOSES = {
    "register",
    "login",
    "reset_password",
    "bind",
    "update_email",
}
_DEFAULT_PREFIX = "sms"


class SmsVerificationError(Exception):
    """Base error for SMS verification failures."""


class SmsSendError(SmsVerificationError):
    """Raised when the upstream SMS service rejects the request."""


@dataclass
class SmsSendResult:
    success: bool
    detail: str = ""
    request_id: Optional[str] = None


def _get_setting(name: str, default):
    return getattr(settings, name, default)


def _code_ttl() -> int:
    return int(_get_setting("SMS_CODE_TTL_SECONDS", 300))


def _default_region_code() -> str:
    return _get_setting("SMS_DEFAULT_REGION_CODE", "+86")


def _redis_url() -> str:
    return _get_setting("REDIS_URL", os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"))


class VerificationCodeStore:

    def __init__(self, prefix: str = _DEFAULT_PREFIX):
        self.prefix = prefix
        self._client: Optional["redis.Redis"] = None
        self._memory_store: dict[str, tuple[str, timezone.datetime]] = {}

    def _get_client(self) -> Optional["redis.Redis"]:
        if redis is None:
            return None
        if self._client is None:
            try:
                self._client = redis.Redis.from_url(_redis_url(), decode_responses=True)
            except Exception as exc:
                logger.warning("无法创建redis代理: %s", exc)
                self._client = None
        return self._client

    def _key(self, identifier: str, purpose: str) -> str:
        normalized = identifier.strip().lower()
        digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
        return f"{self.prefix}:{purpose}:{digest}"

    def _purge_expired(self) -> None:
        now = timezone.now()
        expired = [key for key, (_, ts) in self._memory_store.items() if ts <= now]
        for key in expired:
            self._memory_store.pop(key, None)

    def set(self, phone: str, purpose: str, hashed_code: str, ttl: int) -> None:
        key = self._key(phone, purpose)
        client = self._get_client()
        if client is not None:
            try:
                client.setex(key, ttl, hashed_code)
                return
            except Exception as exc:
                logger.warning("没有redis服务，回到in-memory存储: %s", exc)
                self._client = None
        expires_at = timezone.now() + timezone.timedelta(seconds=ttl)
        self._memory_store[key] = (hashed_code, expires_at)

    def get(self, phone: str, purpose: str) -> Optional[str]:
        key = self._key(phone, purpose)
        client = self._get_client()
        if client is not None:
            try:
                value = client.get(key)
                if value is not None:
                    return value
            except Exception as exc:
                logger.warning("没有redis服务，回到in-memory存储: %s", exc)
                self._client = None
        self._purge_expired()
        data = self._memory_store.get(key)
        if data:
            hashed_code, expires_at = data
            if expires_at > timezone.now():
                return hashed_code
            self._memory_store.pop(key, None)
        return None

    def delete(self, phone: str, purpose: str) -> None:
        key = self._key(phone, purpose)
        client = self._get_client()
        if client is not None:
            try:
                client.delete(key)
            except Exception as exc:
                logger.warning("删除键无redis服务: %s", exc)
                self._client = None
        self._memory_store.pop(key, None)


_store = VerificationCodeStore()
_tencent_client: Optional["SmsClient"] = None


def _normalize_purpose(purpose: str) -> str:
    if not purpose:
        raise ValueError("purpose 不能为空")
    normalized = purpose.strip().lower()
    if normalized not in ALLOWED_PURPOSES:
        raise ValueError(f"purpose 仅支持 {', '.join(sorted(ALLOWED_PURPOSES))}")
    return normalized


def _normalize_email(email: str) -> str:
    if not email:
        raise ValueError("邮箱不能为空")
    normalized = email.strip().lower()
    try:
        validate_email(normalized)
    except ValidationError as exc:
        raise ValueError("邮箱格式不正确") from exc
    return normalized


def _email_subject() -> str:
    return getattr(settings, "EMAIL_VERIFICATION_SUBJECT", "Your Wangumi verification code")


def _email_body(code: str, ttl_seconds: int) -> str:
    ttl_minutes = max(int(ttl_seconds / 60), 1)
    template = getattr(
        settings,
        "EMAIL_VERIFICATION_BODY_TEMPLATE",
        "您的验证码为 {code}，有效期 {ttl} 分钟。如非本人操作请忽略本邮件。",
    )
    try:
        return template.format(code=code, ttl=ttl_minutes)
    except Exception:
        return f"您的验证码为 {code}，有效期 {ttl_minutes} 分钟。"


def _hash_code(phone: str, purpose: str, code: str) -> str:
    secret = getattr(settings, "SMS_CODE_SECRET", settings.SECRET_KEY)
    payload = f"{purpose}:{phone}:{code}:{secret}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _get_tencent_client() -> Optional["SmsClient"]:
    global _tencent_client
    if _tencent_client is not None:
        return _tencent_client
    required = [
        getattr(settings, "TENCENT_SMS_SECRET_ID", None),
        getattr(settings, "TENCENT_SMS_SECRET_KEY", None),
        getattr(settings, "TENCENT_SMS_SDK_APP_ID", None),
        getattr(settings, "TENCENT_SMS_SIGN_NAME", None),
        getattr(settings, "TENCENT_SMS_TEMPLATE_ID", None),
    ]
    if SmsClient is None or any(item in (None, "") for item in required):
        return None
    cred = credential.Credential(
        settings.TENCENT_SMS_SECRET_ID, settings.TENCENT_SMS_SECRET_KEY
    )
    http_profile = HttpProfile(endpoint=getattr(settings, "TENCENT_SMS_ENDPOINT", "sms.tencentcloudapi.com"))
    client_profile = ClientProfile(httpProfile=http_profile)
    region = getattr(settings, "TENCENT_SMS_REGION", "ap-guangzhou")
    _tencent_client = SmsClient(cred, region, client_profile)
    return _tencent_client


def _send_via_tencent(phone: str, code: str) -> SmsSendResult:
    client = _get_tencent_client()
    if client is None or sms_models is None:
        logger.info("腾讯服务未注册 %s", phone)
        return SmsSendResult(success=True, detail="skip (not configured)")
    request = sms_models.SendSmsRequest()
    request.SmsSdkAppId = settings.TENCENT_SMS_SDK_APP_ID
    request.SignName = settings.TENCENT_SMS_SIGN_NAME
    request.TemplateId = settings.TENCENT_SMS_TEMPLATE_ID
    ttl_minutes = max(int(_code_ttl() / 60), 1)
    request.TemplateParamSet = [code, str(ttl_minutes)]
    request.PhoneNumberSet = [_normalize_phone(phone)]
    response = client.SendSms(request)
    if not response.SendStatusSet:
        raise SmsSendError("短信服务商未返回结果")
    status = response.SendStatusSet[0]
    success = getattr(status, "Code", "") == "Ok"
    detail = getattr(status, "Message", "")
    request_id = getattr(response, "RequestId", None)
    if not success:
        raise SmsSendError(detail or "短信发送失败")
    return SmsSendResult(success=True, detail=detail, request_id=request_id)


def send_email_code(email: str, purpose: str, requester_ip: Optional[str] = None) -> SmsSendResult:
    normalized_purpose = _normalize_purpose(purpose)
    normalized_email = _normalize_email(email)
    enforce_verification_code_rate_limits(normalized_email, normalized_purpose, requester_ip)
    code = _generate_code()
    hashed = _hash_code(normalized_email, normalized_purpose, code)
    ttl = _code_ttl()
    _store.set(normalized_email, normalized_purpose, hashed, ttl)
    try:
        sent = send_mail(
            subject=_email_subject(),
            message=_email_body(code, ttl),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@wangumi.local"),
            recipient_list=[normalized_email],
        )
    except Exception as exc:
        _store.delete(normalized_email, normalized_purpose)
        raise SmsSendError("邮件发送失败，请稍后再试") from exc
    if sent == 0:
        _store.delete(normalized_email, normalized_purpose)
        raise SmsSendError("邮件发送失败，请稍后再试")
    if settings.DEBUG:
        logger.debug("Email code %s sent to %s for %s", code, normalized_email, normalized_purpose)
    return SmsSendResult(success=True, detail="email")


def verify_email_code(email: str, purpose: str, code: str, consume: bool = True) -> bool:
    normalized_purpose = _normalize_purpose(purpose)
    normalized_email = _normalize_email(email)
    return _verify_code(normalized_email, normalized_purpose, code, consume)


def _verify_code(identifier: str, purpose: str, code: str, consume: bool) -> bool:
    if not code:
        return False
    stored_hash = _store.get(identifier, purpose)
    if not stored_hash:
        return False
    provided_hash = _hash_code(identifier, purpose, code)
    if stored_hash != provided_hash:
        return False
    if consume:
        _store.delete(identifier, purpose)
    return True
