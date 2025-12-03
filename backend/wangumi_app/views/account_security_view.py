from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.services.session_security import invalidate_user_sessions_and_tokens


class PasswordChangeView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        user = request.user
        old_password = (request.data.get("old_password") or "").strip()
        new_password = (request.data.get("new_password") or "").strip()

        if not old_password or not new_password:
            return Response(
                {"error": "旧密码和新密码均不能为空"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if old_password == new_password:
            return Response(
                {"error": "新密码需与旧密码不同"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.check_password(old_password):
            return Response(
                {"error": "无法更新密码，请检查输入"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            password_validation.validate_password(new_password, user=user)
        except ValidationError as exc:
            return Response(
                {"error": "；".join(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        invalidate_user_sessions_and_tokens(user)
        return Response(
            {"message": "密码已更新，请重新登录"},
            status=status.HTTP_200_OK,
        )
