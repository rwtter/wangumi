from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import UserProfile
from wangumi_app.services import (
    RateLimitError,
    SmsSendError,
    send_email_code,
    verify_email_code,
)
from wangumi_app.views.utils import get_client_ip

User = get_user_model()


class ContactChangeRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        contact_type = (request.data.get("contact_type") or "").strip().lower()
        new_value = (request.data.get("value") or "").strip()
        current_password = request.data.get("current_password") or ""

        error = _validate_identity(user, current_password)
        if error:
            return error

        if contact_type != "email":
            return Response({"error": "仅支持邮箱验证"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            normalized_value = _normalize_email(new_value)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if (user.email or "").strip().lower() == normalized_value:
            return Response({"error": "新邮箱不能与当前邮箱相同"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=normalized_value).exclude(pk=user.pk).exists():
            return Response({"error": "该邮箱已被使用"}, status=status.HTTP_409_CONFLICT)

        client_ip = get_client_ip(request)
        try:
            send_email_code(normalized_value, "update_email", requester_ip=client_ip)
        except RateLimitError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except SmsSendError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "验证码已发送，请查收"}, status=status.HTTP_200_OK)


class ContactChangeConfirmView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        contact_type = (request.data.get("contact_type") or "").strip().lower()
        new_value = (request.data.get("value") or "").strip()
        code = (request.data.get("code") or "").strip()
        current_password = request.data.get("current_password") or ""

        if not code:
            return Response({"error": "验证码不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        error = _validate_identity(user, current_password)
        if error:
            return error

        if contact_type != "email":
            return Response({"error": "仅支持邮箱验证"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            normalized_value = _normalize_email(new_value)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if (user.email or "").strip().lower() == normalized_value:
            return Response({"error": "新邮箱不能与当前邮箱相同"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=normalized_value).exclude(pk=user.pk).exists():
            return Response({"error": "该邮箱已被使用"}, status=status.HTTP_409_CONFLICT)

        verified = verify_email_code(normalized_value, "update_email", code, consume=True)
        if not verified:
            return Response({"error": "验证码无效或已过期"}, status=status.HTTP_400_BAD_REQUEST)

        user.email = normalized_value
        user.save(update_fields=["email"])

        try:
            cellphone = user.userprofile.cellphone
        except UserProfile.DoesNotExist:
            cellphone = None
        data = {
            "username": user.username,
            "email": user.email,
            "cellphone": cellphone,
        }
        return Response({"message": "联系方式已更新", "data": data}, status=status.HTTP_200_OK)


def _validate_identity(user, password):
    if not password or not user.check_password(password):
        return Response(
            {"error": "身份验证失败，请重新输入当前密码"},
            status=status.HTTP_403_FORBIDDEN,
        )
    return None


def _normalize_email(value: str) -> str:
    if not value:
        raise ValueError("邮箱不能为空")
    try:
        validate_email(value)
    except ValidationError as exc:
        raise ValueError("邮箱格式不正确") from exc
    return value.strip().lower()
