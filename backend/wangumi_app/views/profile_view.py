from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# 新增：显式使用 SimpleJWT 的认证类
from rest_framework_simplejwt.authentication import JWTAuthentication

User = get_user_model()


def _build_profile_dict(user: "User", is_self: bool) -> Dict[str, Any]:
    """
    将用户与其 Profile 安全地拼成可返回的 dict。
    - is_self=True 时，可返回更多仅本人可见的信息（例如邮箱、私密签名等——如果模型里有）
    - 所有字段都用 getattr 访问，避免模型字段差异导致崩溃
    """
    profile = getattr(user, "userprofile", None)

    def g(obj, name, default=None):
        return getattr(obj, name, default) if obj is not None else default

    # 头像 URL 友好化
    avatar_url = None
    raw_avatar = g(profile, "avatar")
    if raw_avatar:
        try:
            avatar_url = raw_avatar.url  # Image/FileField
        except Exception:
            avatar_url = str(raw_avatar)

    # 关注/粉丝数：尽量兼容不同 related_name
    def _safe_count(obj_name_candidates):
        for cand in obj_name_candidates:
            rel = getattr(user, cand, None)
            try:
                if rel is not None:
                    return rel.count()
            except Exception:
                pass
        return 0

    following_count = _safe_count(["following", "followings", "following_set"])
    follower_count = _safe_count(["followers", "follower", "followers_set"])

    base = {
        "id": user.id,
        "username": getattr(user, "username", None),
        "nickname": g(profile, "nickname", g(profile, "display_name", None)),
        "avatar": avatar_url,
        "bio": g(profile, "bio", g(profile, "intro", None)),
        "signature": g(profile, "signature", None),
        "gender": g(profile, "gender", None),
        "location": g(profile, "location", None),
        "website": g(profile, "website", None),
        "following_count": following_count,
        "follower_count": follower_count,
    }

    if is_self:
        # 仅本人可见：邮箱、手机等（如果模型或 User 上存在）
        base.update({
            "email": getattr(user, "email", None),
            "cellphone": g(profile, "cellphone", None),
            "qq": g(profile, "qq", None),
            "weixin": g(profile, "weixin", None),
            "weibo": g(profile, "weibo", None),
            # 也可返回隐私设置（若模型存在）
            "privacy": {
                "follows": g(profile, "privacy_follows", None),
                "followers": g(profile, "privacy_followers", None),
                "watchlist": g(profile, "privacy_watchlist", None),
                "activities": g(profile, "privacy_activities", None),
            },
        })

    return base


def _ok(data: Any, message: str = "success", code: int = 0, http_status=status.HTTP_200_OK):
    """
    统一返回结构：
    {
      "code": 0,
      "message": "success",
      "data": {...}
    }
    """
    return Response({"code": code, "message": message, "data": data}, status=http_status)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    user = request.user
    file = request.FILES.get("avatar")

    if not file:
        return Response({"message": "未上传头像文件"}, status=400)

    # 保存文件到模型
    user.avatar = file
    user.save()

    return Response({
        "message": "上传成功",
        "avatar_url": user.avatar.url
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def profile_by_user_id(request, user_id: int):
    """
    GET /api/users/<user_id>/profile
    查看任意用户主页（公开信息）。
    """
    user = get_object_or_404(User, pk=user_id)
    data = _build_profile_dict(user, is_self=(request.user.is_authenticated and request.user.id == user.id))
    return _ok(data)


@api_view(["GET"])
@authentication_classes([JWTAuthentication])   # 新增：使用 JWT 做认证
@permission_classes([IsAuthenticated])
def my_profile(request):
    """
    GET /api/user/profile
    查看自己的主页（包含仅本人可见字段）。
    需要登录（JWT Bearer Token）。
    """
    data = _build_profile_dict(request.user, is_self=True)
    return _ok(data)
