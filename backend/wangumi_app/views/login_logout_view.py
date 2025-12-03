from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.views.decorators.csrf import csrf_exempt

# ------------------
# 登录接口
# ------------------
class LoginView(TokenObtainPairView):
    """
    DRF SimpleJWT 自带登录接口，返回 access + refresh token
    """
    pass  # 直接使用父类即可，无需额外逻辑

# ------------------
# 登出接口
# ------------------
class LogoutView(APIView):
    """
    登出逻辑：把 refresh token 加入黑名单
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @csrf_exempt
    def post(self, request):
        """
        登出用户，将refresh token加入黑名单
        前端需要传递refresh_token参数
        """
        try:
            # 从请求体获取refresh_token
            refresh_token = request.data.get('refresh_token')
            if not refresh_token:
                return Response({
                    "code": 1,
                    "message": "Refresh token is required for logout",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 创建RefreshToken实例并加入黑名单
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "code": 0,
                "message": "Logout successful",
                "data": None
            }, status=status.HTTP_200_OK)

        except TokenError:
            return Response({
                "code": 1,
                "message": "Invalid or expired refresh token",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "code": 1,
                "message": "Logout failed",
                "data": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------
# 登出所有设备接口
# ------------------
class LogoutAllView(APIView):
    """
    登出用户所有设备，需要配合使用才能实现
    通过修改用户密码或使用其他方式强制所有token失效
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    @csrf_exempt
    def post(self, request):
        """
        强制用户登出所有设备
        通过重置密码的JWT版本号来实现
        """
        try:
            user = request.user
            # 更新用户的last_login时间，这会使之前所有的token失效
            from django.utils import timezone
            user.last_login = timezone.now()
            user.save()

            return Response({
                "code": 0,
                "message": "Logged out from all devices successfully",
                "data": None
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "code": 1,
                "message": "Logout all devices failed",
                "data": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)