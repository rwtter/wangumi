# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()

class PrivacyViewTests(TestCase):
    def setUp(self):
        # 创建用户并登录获取 Token
        self.client = Client()
        self.user = User.objects.create_user(username="privacy_user", password="123456")
        resp = self.client.post("/api/login/", {"username": "privacy_user", "password": "123456"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200, "登录失败，无法获取 JWT Token")
        self.token = resp.json()["access"]

    def auth_header(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_get_privacy_defaults(self):
        """测试默认隐私设置获取"""
        resp = self.client.get("/api/users/privacy", **self.auth_header())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # 默认情况下，所有隐私设置应为 "public"
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["followings"], "public")
        self.assertEqual(data["data"]["followers"], "public")
        self.assertEqual(data["data"]["watchlist"], "public")
        self.assertEqual(data["data"]["activities"], "public")

    def test_update_privacy_success(self):
        """测试成功更新部分隐私设置"""
        payload = {"followers": "private", "watchlist": "mutual"}
        resp = self.client.put("/api/users/privacy", payload, content_type="application/json", **self.auth_header())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # 验证返回的数据中对应字段已更新
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["followers"], "private")
        self.assertEqual(data["data"]["watchlist"], "mutual")
        # 其他未提供的字段应保持默认值
        self.assertEqual(data["data"]["followings"], "public")
        self.assertEqual(data["data"]["activities"], "public")

    def test_update_privacy_invalid_field(self):
        """测试提供无效字段名时的错误"""
        payload = {"invalid_field": "public"}
        resp = self.client.put("/api/users/privacy", payload, content_type="application/json", **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("unsupported field", resp.json().get("message", ""))

    def test_update_privacy_invalid_value(self):
        """测试提供无效字段值时的错误"""
        payload = {"followers": "unknown"}
        resp = self.client.put("/api/users/privacy", payload, content_type="application/json", **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("invalid value", resp.json().get("message", ""))

    def test_privacy_unauthorized(self):
        """测试未登录用户无法访问隐私设置接口"""
        # 未提供认证令牌的请求
        resp_get = self.client.get("/api/users/privacy")
        resp_put = self.client.put("/api/users/privacy", {"followers": "private"}, content_type="application/json")
        # 对于未认证用户，应该返回 401 或 403
        self.assertIn(resp_get.status_code, [401, 403])
        self.assertIn(resp_put.status_code, [401, 403])
