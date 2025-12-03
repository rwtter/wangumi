# backend/wangumi_app/views/follow_view.py
# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.request import Request
from rest_framework.response import Response

from rest_framework_simplejwt.authentication import JWTAuthentication  # 和 profile_view 一样

from wangumi_app.models import UserFollow  # 你们项目里的关注关系模型

User = get_user_model()


def _ok(data=None, message: str = "success", code: int = 0,
        http_status: int = status.HTTP_200_OK):
    """
    统一成功返回结构，和 profile_view._ok 保持风格一致
    """
    return Response(
        {"code": code, "message": message, "data": data or {}},
        status=http_status,
    )


def _err(message: str, http_status: int = status.HTTP_400_BAD_REQUEST, code: int = 1):
    """
    统一错误返回结构
    """
    return Response(
        {"code": code, "message": message, "data": {}},
        status=http_status,
    )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])          # ★ 关键：显式使用 JWT
@permission_classes([permissions.IsAuthenticated])    # 只允许登录用户
def follow_user(request: Request, id: int):
    """
    关注用户：
    POST /api/users/<id>/follow

    测试要求：
    - 关注成功：status 200，code == 0，data.success == True
    - 再次关注（幂等）：status 200，仍然 success True
    - 不能关注自己：status 400，code != 0，message 包含 "cannot follow yourself"
    """
    me = request.user
    target_user = get_object_or_404(User, id=id)

    # 不能关注自己
    if target_user.id == me.id:
        return _err("cannot follow yourself", http_status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            # 如果已存在则抛 IntegrityError 或 get_or_create 幂等处理
            UserFollow.objects.get_or_create(
                follower=me,
                following=target_user,
            )
    except IntegrityError:
        # 已经关注过了，当作幂等成功
        pass

    return _ok({"success": True})


@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])          # ★ 关键：显式使用 JWT
@permission_classes([permissions.IsAuthenticated])
def unfollow_user(request: Request, id: int):
    """
    取消关注：
    DELETE /api/users/<id>/unfollow

    测试要求：
    - 取消成功：status 200，code == 0，data.success == True
    - 再次取消（幂等）：status 200，仍然 success True
    """
    me = request.user
    target_user = get_object_or_404(User, id=id)

    with transaction.atomic():
        UserFollow.objects.filter(
            follower=me,
            following=target_user,
        ).delete()

    return _ok({"success": True})
