# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from wangumi_app.models import UserFollow

User = get_user_model()

class FollowViewTests(TestCase):
    def setUp(self):
        # 创建两个用户：follower 用户和 target 用户
        self.client = Client()
        self.user_follower = User.objects.create_user(username="follower", password="123456")
        self.user_target = User.objects.create_user(username="target", password="123456")
        # 登录 follower 用户获取 JWT
        resp = self.client.post("/api/login/", {"username": "follower", "password": "123456"}, content_type="application/json")
        self.assertEqual(resp.status_code, 200, "登录失败，无法获取 JWT Token")
        self.token = resp.json()["access"]

    def auth_header(self):
        return {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_follow_success_and_idempotent(self):
        """测试关注成功和幂等行为"""
        url = f"/api/users/{self.user_target.id}/follow"
        # 第一次关注
        resp1 = self.client.post(url, **self.auth_header())
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["code"], 0)
        self.assertTrue(data1["data"].get("success", False))
        # 验证数据库中创建了关注关系
        exists = UserFollow.objects.filter(follower=self.user_follower, following=self.user_target).exists()
        self.assertTrue(exists, "关注关系未正确创建")

        # 重复关注同一用户
        resp2 = self.client.post(url, **self.auth_header())
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["code"], 0)
        self.assertTrue(data2["data"].get("success", False))
        # 数据库中仍应只有一条关注记录（没有重复）
        count = UserFollow.objects.filter(follower=self.user_follower, following=self.user_target).count()
        self.assertEqual(count, 1, "不应存在重复的关注关系记录")

    def test_unfollow_success_and_idempotent(self):
        """测试取消关注成功以及幂等"""
        url = f"/api/users/{self.user_target.id}/unfollow"
        # 预先创建关注关系
        UserFollow.objects.create(follower=self.user_follower, following=self.user_target)
        # 取消关注
        resp1 = self.client.delete(url, **self.auth_header())
        self.assertEqual(resp1.status_code, 200)
        data1 = resp1.json()
        self.assertEqual(data1["code"], 0)
        self.assertTrue(data1["data"].get("success", False))
        # 验证数据库中关注关系已删除
        exists = UserFollow.objects.filter(follower=self.user_follower, following=self.user_target).exists()
        self.assertFalse(exists, "关注关系应已删除")

        # 再次对同一用户执行取消关注（此时已不存在关注关系）
        resp2 = self.client.delete(url, **self.auth_header())
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.json()
        self.assertEqual(data2["code"], 0)
        self.assertTrue(data2["data"].get("success", False))
        # 数据库中仍无关注记录（无错误产生）
        count = UserFollow.objects.filter(follower=self.user_follower, following=self.user_target).count()
        self.assertEqual(count, 0)

    def test_follow_self_forbidden(self):
        """测试无法关注自己"""
        url = f"/api/users/{self.user_follower.id}/follow"
        resp = self.client.post(url, **self.auth_header())
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        # code 不为0，message 提示不能关注自己
        self.assertNotEqual(data["code"], 0)
        self.assertIn("cannot follow yourself", data["message"])

    def test_follow_unfollow_unauthorized(self):
        """测试未登录时关注/取消关注接口返回 401/403"""
        follow_url = f"/api/users/{self.user_target.id}/follow"
        unfollow_url = f"/api/users/{self.user_target.id}/unfollow"
        resp1 = self.client.post(follow_url)      # 未提供认证
        resp2 = self.client.delete(unfollow_url)  # 未提供认证
        self.assertIn(resp1.status_code, [401, 403])
        self.assertIn(resp2.status_code, [401, 403])
