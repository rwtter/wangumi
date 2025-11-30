from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
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
    #permission_classes = [permissions.IsAuthenticated]
    #authentication_classes = [JWTAuthentication]
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    @csrf_exempt

    def post(self, request):
        # 不去验证 refresh，不操作黑名单，只告诉前端成功
        return Response({"message": "Logout successful."}, status=200)