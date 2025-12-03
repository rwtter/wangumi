# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from django.core.files.uploadedfile import UploadedFile
from PIL import Image

from wangumi_app.models import UserProfile

User = get_user_model()


def ok(data=None, message="success"):
    return Response(
        {"code": 0, "message": message, "data": data or {}},
        status=status.HTTP_200_OK,
    )


def err(message, http_status=status.HTTP_400_BAD_REQUEST, code=1, data=None):
    return Response(
        {"code": code, "message": message, "data": data or {}},
        status=http_status,
    )


class ProfileEditView(APIView):
    """
    POST /api/user/profile
    - 更新用户名（展示名）、昵称、个性签名、个人简介、联系方式、个人站点、性别、地区
    约束：
      * 用户名长度 ≤ 20
      * 昵称长度 ≤ 50
      * 个性签名长度 ≤ 50
      * 用户名需要在全站唯一（排除自己）
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @transaction.atomic
    def post(self, request):
        user: User = request.user
        # 确保有 profile 记录（测试用例里通过 user.profile 访问）
        profile, _ = UserProfile.objects.get_or_create(user=user)

        username = request.data.get("username", "").strip()
        nickname = request.data.get("nickname", "").strip()
        signature = request.data.get("signature", "").strip()
        intro = request.data.get("intro", "").strip()

        # 联系方式
        cellphone = request.data.get("cellphone", "").strip()
        qq = request.data.get("qq", "").strip()
        weixin = request.data.get("weixin", "").strip()
        weibo = request.data.get("weibo", "").strip()

        # 其他信息
        website = request.data.get("website", "").strip()
        gender = request.data.get("gender", "").strip()
        location = request.data.get("location", "").strip()

        # 长度校验
        if len(username) > 20 or len(nickname) > 50 or len(signature) > 50:
            return err(
                "用户名长度需 ≤ 20，昵称长度需 ≤ 50，个性签名长度需 ≤ 50",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 用户名唯一性校验（排除自己）
        if username and username != user.username:
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                return err(
                    "用户名已被占用",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

        # 更新用户名
        if username:
            user.username = username
            user.save(update_fields=["username"])

        # 更新 profile
        profile.nickname = nickname
        profile.signature = signature
        profile.intro = intro
        profile.cellphone = cellphone
        profile.qq = qq
        profile.weixin = weixin
        profile.weibo = weibo
        profile.website = website
        profile.gender = gender
        profile.location = location
        profile.save()

        data = {
            "username": user.username,
            "nickname": profile.nickname or "",
            "signature": profile.signature or "",
            "intro": profile.intro or "",
            "cellphone": profile.cellphone or "",
            "qq": profile.qq or "",
            "weixin": profile.weixin or "",
            "weibo": profile.weibo or "",
            "website": profile.website or "",
            "gender": profile.gender or "",
            "location": profile.location or "",
        }
        return ok(data=data)


class AvatarUploadView(APIView):
    """
    POST /api/user/avatar
    - 上传 / 更新头像
    约束：
      * 仅支持 jpg/jpeg/png
      * 大小 ≤ 2MB
      * 必须为有效图片
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    ALLOWED_EXTS = {"jpg", "jpeg", "png"}

    def post(self, request):
        user: User = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)

        avatar: UploadedFile = request.FILES.get("avatar")
        if not avatar:
            return err(
                "未收到头像文件",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 检查扩展名
        name = avatar.name or ""
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if ext not in self.ALLOWED_EXTS:
            return err(
                "仅支持 jpg/jpeg/png 格式",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 检查大小
        if avatar.size > self.MAX_AVATAR_SIZE:
            return err(
                "文件大小超过 2MB 限制",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 检查是否为有效图片
        try:
            img = Image.open(avatar)
            img.verify()
        except Exception:
            return err(
                "非法图片文件",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 重新把文件指针挪回开头
        avatar.seek(0)

        profile.avatar = avatar
        profile.save(update_fields=["avatar"])

        data = {
            "avatar_url": profile.avatar.url if profile.avatar else "",
        }
        return ok(data=data)
