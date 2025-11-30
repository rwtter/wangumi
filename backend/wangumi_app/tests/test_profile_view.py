# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

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
