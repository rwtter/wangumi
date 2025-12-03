# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from wangumi_app.models import UserProfile

User = get_user_model()


class ProfileViewTests(TestCase):
    def setUp(self):
        """
        创建两个用户：
        - self.user_self : 自己，用来测试 “我的主页”
        - self.user_other: 其他用户，用来测试 “查看他人主页”
        """
        self.client = Client()

        self.user_self = User.objects.create_user(
            username="test_self", password="123456"
        )

        self.user_other = User.objects.create_user(
            username="test_other", password="123456"
        )

        login_resp = self.client.post(
        "/api/login/",
        {"username": "test_self", "password": "123456"},
        content_type="application/json",
    )


        self.assertEqual(
            login_resp.status_code, 200, "登录失败，无法获取 JWT Token"
        )

        self.access_token = login_resp.json()["access"]

    def test_visit_other_profile(self):
        """
        测试：GET /api/users/<id>/profile
        任何用户都可访问（AllowAny）
        """
        url = f"/api/users/{self.user_other.id}/profile"
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["username"], "test_other")

    def test_visit_my_profile(self):
        """
        测试：GET /api/user/profile
        必须携带 JWT Token 才能访问
        """
        resp = self.client.get(
            "/api/user/profile",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["username"], "test_self")

    def test_visit_my_profile_without_token(self):
        """
        测试：未携带 token 时访问 /api/user/profile，应返回 401
        """
        resp = self.client.get("/api/user/profile")

        self.assertIn(resp.status_code, [401, 403])

    def test_profile_edit_with_new_fields(self):
        """
        测试：POST /api/user/profile 更新所有新增字段
        """
        # 确保用户有profile记录
        profile, _ = UserProfile.objects.get_or_create(user=self.user_self)

        # 测试数据
        update_data = {
            "username": "updated_self",
            "nickname": "测试昵称",
            "signature": "这是个性签名",
            "intro": "这是个人简介",
            "cellphone": "13800138000",
            "qq": "123456789",
            "weixin": "test_weixin",
            "weibo": "test_weibo",
            "website": "https://example.com",
            "gender": "男",
            "location": "北京"
        }

        resp = self.client.post(
            "/api/user/profile/edit",
            update_data,
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # 验证返回数据
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["username"], "updated_self")
        self.assertEqual(data["data"]["nickname"], "测试昵称")
        self.assertEqual(data["data"]["signature"], "这是个性签名")
        self.assertEqual(data["data"]["intro"], "这是个人简介")
        self.assertEqual(data["data"]["cellphone"], "13800138000")
        self.assertEqual(data["data"]["qq"], "123456789")
        self.assertEqual(data["data"]["weixin"], "test_weixin")
        self.assertEqual(data["data"]["weibo"], "test_weibo")
        self.assertEqual(data["data"]["website"], "https://example.com")
        self.assertEqual(data["data"]["gender"], "男")
        self.assertEqual(data["data"]["location"], "北京")

        # 验证数据库中的数据
        updated_user = User.objects.get(id=self.user_self.id)
        updated_profile = UserProfile.objects.get(user=updated_user)
        self.assertEqual(updated_user.username, "updated_self")
        self.assertEqual(updated_profile.nickname, "测试昵称")
        self.assertEqual(updated_profile.signature, "这是个性签名")
        self.assertEqual(updated_profile.intro, "这是个人简介")
        self.assertEqual(updated_profile.cellphone, "13800138000")
        self.assertEqual(updated_profile.qq, "123456789")
        self.assertEqual(updated_profile.weixin, "test_weixin")
        self.assertEqual(updated_profile.weibo, "test_weibo")
        self.assertEqual(updated_profile.website, "https://example.com")
        self.assertEqual(updated_profile.gender, "男")
        self.assertEqual(updated_profile.location, "北京")

    def test_profile_edit_length_validation(self):
        """
        测试：字段长度校验
        """
        # 测试超长昵称
        long_nickname = "a" * 51  # 超过50个字符
        resp = self.client.post(
            "/api/user/profile/edit",
            {"nickname": long_nickname},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["code"], 1)
        self.assertIn("昵称长度需 ≤ 50", resp.json()["message"])

    def test_profile_edit_partial_update(self):
        """
        测试：部分字段更新
        """
        # 确保用户有profile记录
        profile, _ = UserProfile.objects.get_or_create(user=self.user_self)

        # 只更新部分字段
        resp = self.client.post(
            "/api/user/profile/edit",
            {
                "nickname": "部分更新昵称",
                "qq": "987654321"
            },
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
            content_type="application/json",
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        # 验证更新的字段
        self.assertEqual(data["data"]["nickname"], "部分更新昵称")
        self.assertEqual(data["data"]["qq"], "987654321")

        # 验证其他字段保持不变
        self.assertEqual(data["data"]["username"], self.user_self.username)
