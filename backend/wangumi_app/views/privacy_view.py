# backend/wangumi_app/views/privacy_view.py
# -*- coding: utf-8 -*-
from typing import Any, Dict

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework_simplejwt.authentication import JWTAuthentication   # ★必须添加

from wangumi_app.models import PrivacySetting

# 可选的可见性取值集合
VIS_CHOICES = {"self", "mutual", "public","friends"}  # 仅自己/互关可见/所有人可见

def _ok(data: Dict[str, Any] = None):
    return Response({"code": 0, "message": "success", "data": data or {}}, status=status.HTTP_200_OK)

def _err(msg: str, http_status=status.HTTP_400_BAD_REQUEST, code: int = 1):
    return Response({"code": code, "message": msg, "data": {}}, status=http_status)


@api_view(["GET", "PUT"])
@authentication_classes([JWTAuthentication])          # ★★★ 加上 JWT 认证 ★★★
@permission_classes([permissions.IsAuthenticated])     # 保持原有权限判断
def privacy_settings(request: Request):
    """
    GET /api/users/privacy    - 获取当前用户的隐私设置
    PUT /api/users/privacy    - 更新当前用户的隐私设置
    """
    # GET —— 读取默认隐私设置
    if request.method == "GET":
        ps, _ = PrivacySetting.objects.get_or_create(user=request.user)
        data = {
            "followings": ps.followings,
            "followers": ps.followers,
            "watchlist": ps.watchlist,
            "activities": ps.activities,
        }
        return _ok(data)

    # PUT —— 更新隐私设置
    if request.method == "PUT":
        payload = request.data or {}
        for key, val in payload.items():
            if key not in {"followings", "followers", "watchlist", "activities"}:
                return _err(f"unsupported field: {key}")
            if val not in VIS_CHOICES:
                return _err(f"invalid value for {key}: {val}")

        # 原子更新
        with transaction.atomic():
            ps, _ = PrivacySetting.objects.select_for_update().get_or_create(user=request.user)
            for k, v in payload.items():
                setattr(ps, k, v)
            ps.save()

        data = {
            "followings": ps.followings,
            "followers": ps.followers,
            "watchlist": ps.watchlist,
            "activities": ps.activities,
        }
        return _ok(data)
