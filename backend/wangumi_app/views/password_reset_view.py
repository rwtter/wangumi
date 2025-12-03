import json

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from wangumi_app.services import (
    RateLimitError,
    SmsSendError,
    send_email_code,
    verify_email_code,
)
from wangumi_app.services.session_security import invalidate_user_sessions_and_tokens
from wangumi_app.views.utils import get_client_ip


def _parse_request_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("请求数据格式错误") from exc


def _normalize_email_for_lookup(email: str) -> str:
    try:
        validate_email(email or "")
    except ValidationError as exc:
        raise ValueError("邮箱格式不正确") from exc
    return (email or "").strip().lower()


@csrf_exempt
def request_password_reset(request):
    if request.method != "POST":
        return JsonResponse({"error": "仅支持POST请求"}, status=405, json_dumps_params={"ensure_ascii": False})
    try:
        data = _parse_request_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})

    email = data.get("email")
    if not email:
        return JsonResponse({"error": "邮箱不能为空"}, status=400, json_dumps_params={"ensure_ascii": False})

    try:
        normalized_email = _normalize_email_for_lookup(email)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})

    ip_address = get_client_ip(request)
    user_exists = User.objects.filter(email__iexact=normalized_email).exists()
    if user_exists:
        try:
            send_email_code(normalized_email, "reset_password", requester_ip=ip_address)
        except RateLimitError as exc:
            return JsonResponse({"error": str(exc)}, status=429, json_dumps_params={"ensure_ascii": False})
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})
        except SmsSendError as exc:
            return JsonResponse({"error": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})

    # 为避免信息泄露，即使邮箱不存在也返回成功
    return JsonResponse(
        {"message": "如果该邮箱存在，我们已发送验证码"},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )


@csrf_exempt
def confirm_password_reset(request):
    if request.method != "POST":
        return JsonResponse({"error": "仅支持POST请求"}, status=405, json_dumps_params={"ensure_ascii": False})
    try:
        data = _parse_request_body(request)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})

    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    if not email:
        return JsonResponse({"error": "邮箱不能为空"}, status=400, json_dumps_params={"ensure_ascii": False})
    if not code:
        return JsonResponse({"error": "验证码不能为空"}, status=400, json_dumps_params={"ensure_ascii": False})
    if not new_password or len(new_password) < 6:
        return JsonResponse({"error": "新密码长度至少6位"}, status=400, json_dumps_params={"ensure_ascii": False})

    try:
        normalized_email = _normalize_email_for_lookup(email)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})

    try:
        is_valid = verify_email_code(normalized_email, "reset_password", code, consume=True)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400, json_dumps_params={"ensure_ascii": False})

    if not is_valid:
        return JsonResponse({"error": "验证码无效或已过期"}, status=400, json_dumps_params={"ensure_ascii": False})

    try:
        user = User.objects.get(email__iexact=normalized_email)
    except User.DoesNotExist:
        return JsonResponse({"error": "账号不存在"}, status=404, json_dumps_params={"ensure_ascii": False})

    user.set_password(new_password)
    user.save(update_fields=["password"])
    invalidate_user_sessions_and_tokens(user)

    return JsonResponse(
        {"message": "密码已重置，请重新登录"},
        status=200,
        json_dumps_params={"ensure_ascii": False},
    )
