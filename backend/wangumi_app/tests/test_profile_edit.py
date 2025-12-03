# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
import io, os

from wangumi_app.models import UserProfile

User = get_user_model()

class ProfileEditViewTests(TestCase):
    def setUp(self):
        # 创建两个用户：一个作为自己（用于登录编辑），另一个用于测试用户名唯一性约束
        self.client = Client()
        self.user_main = User.objects.create_user(username="main_user", password="123456")
        self.user_other = User.objects.create_user(username="other_user", password="123456")
        # 获取 JWT token（登录 main_user）
        resp = self.client.post("/api/login/", {"username": "main_user", "password": "123456"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200, "登录失败，无法获取 JWT Token")
        self.token = resp.json().get("access")

    def auth_header(self):
        """辅助方法：返回包含认证头的字典"""
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_update_profile_success(self):
        """测试成功更新用户名、签名和介绍"""
        payload = {
            "username": "new_username",
            "signature": "新签名",
            "intro": "这是新的个人介绍"
        }
        resp = self.client.post("/api/user/profile/edit", payload, **self.auth_header())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # 验证响应结构与更新结果
        self.assertEqual(data["code"], 0)
        self.assertEqual(data["data"]["username"], "new_username")
        self.assertEqual(data["data"]["signature"], "新签名")
        self.assertEqual(data["data"]["intro"], "这是新的个人介绍")
        # 数据库中的用户信息也应更新
        self.user_main.refresh_from_db()
        self.assertEqual(self.user_main.username, "new_username")
        # Profile 签名和介绍
        profile = UserProfile.objects.filter(user=self.user_main).first()
        self.assertIsNotNone(profile, "UserProfile 未创建")
        self.assertEqual(profile.signature, "新签名")
        self.assertEqual(profile.intro, "这是新的个人介绍")

    def test_update_profile_username_taken(self):
        """测试更新用户名时如果已被占用，返回错误"""
        payload = {"username": "other_user"}  # 尝试将用户名改为已存在的用户名
        resp = self.client.post("/api/user/profile/edit", payload, **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertNotEqual(data["code"], 0)
        self.assertIn("已被占用", data["message"])

    def test_update_profile_invalid_length(self):
        """测试用户名或签名长度超限时的错误返回"""
        long_name = "a" * 21  # 21 characters
        long_sign = "b" * 51  # 51 characters
        # 用户名超长
        resp1 = self.client.post("/api/user/profile/edit", {"username": long_name}, **self.auth_header())
        self.assertEqual(resp1.status_code, 400)
        self.assertIn("用户名长度需 ≤ 20", resp1.json().get("message", ""))
        # 签名超长
        resp2 = self.client.post("/api/user/profile/edit", {"signature": long_sign}, **self.auth_header())
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("个性签名长度需 ≤ 50", resp2.json().get("message", ""))

    def test_update_profile_unauthorized(self):
        """测试未登录用户无法更新个人信息（应返回 401 或 403）"""
        resp = self.client.post("/api/user/profile/edit", {"username": "x"})
        # 未提供认证，应该被拒绝
        self.assertIn(resp.status_code, [401, 403])

    def test_upload_avatar_success(self):
        """测试成功上传头像"""
        # 创建一张简单的图片文件 (PNG)
        img = Image.new("RGB", (100, 100), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        file = SimpleUploadedFile("test.png", buf.getvalue(), content_type="image/png")
        resp = self.client.post("/api/user/avatar", {"avatar": file}, **self.auth_header())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["code"], 0)
        # 返回的 avatar_url 应为非空字符串（图片URL）
        self.assertIsInstance(data["data"].get("avatar_url"), str)
        self.assertTrue(data["data"]["avatar_url"])

    def test_upload_avatar_invalid_format(self):
        """测试上传不支持的文件格式"""
        file = SimpleUploadedFile("test.txt", b"dummy data", content_type="text/plain")
        resp = self.client.post("/api/user/avatar", {"avatar": file}, **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("仅支持 jpg/jpeg/png", resp.json().get("message", ""))

    def test_upload_avatar_oversize(self):
        """测试上传超过大小限制的头像"""
        # 构造一个超过2MB的假文件
        big_content = b"a" * (2 * 1024 * 1024 + 1)  # just over 2MB
        file = SimpleUploadedFile("large.jpg", big_content, content_type="image/jpeg")
        resp = self.client.post("/api/user/avatar", {"avatar": file}, **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("超过 2MB 限制", resp.json().get("message", ""))

    def test_upload_avatar_invalid_image(self):
        """测试上传伪装成图片的无效文件"""
        # 构造一个扩展名正确但内容不是图片的文件
        fake_image = SimpleUploadedFile("fake.png", b"not an image", content_type="image/png")
        resp = self.client.post("/api/user/avatar", {"avatar": fake_image}, **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("非法图片文件", resp.json().get("message", ""))

    def test_upload_avatar_unauthorized(self):
        """测试未登录用户无法上传头像"""
        file = SimpleUploadedFile("test.png", b"dummy", content_type="image/png")
        resp = self.client.post("/api/user/avatar", {"avatar": file})
        self.assertIn(resp.status_code, [401, 403])
