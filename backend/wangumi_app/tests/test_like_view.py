"""
点赞系统测试文件
测试评论的点赞、取消点赞、点赞状态查询等功能
"""

import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    Anime, Comment, Like, UserProfile
)


class LikeViewTests(TestCase):
    """点赞功能测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = Client()

        # 创建测试用户
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="user1@test.com",
            password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="user2@test.com",
            password="testpass123"
        )

        # 创建用户档案
        UserProfile.objects.create(user=self.user1, cellphone="13800000001")
        UserProfile.objects.create(user=self.user2, cellphone="13800000002")

        # 生成JWT token
        self.refresh_token1 = RefreshToken.for_user(self.user1)
        self.access_token1 = str(self.refresh_token1.access_token)

        self.refresh_token2 = RefreshToken.for_user(self.user2)
        self.access_token2 = str(self.refresh_token2.access_token)

        # 创建测试番剧
        self.anime = Anime.objects.create(
            title="测试番剧",
            title_cn="测试番剧中文",
            description="这是一个测试番剧",
            rating=8.5,
            popularity=100
        )

        # 创建测试评论
        self.comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=8,
            content="这是一条测试评论",
            scope='ANIME',
            likes=5  # 初始点赞数
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_like_comment_success(self):
        """测试点赞评论成功"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.post(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "点赞成功")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.comment.id)
        self.assertEqual(response_data['likes_count'], 6)  # 原始5 + 新增1
        self.assertTrue(response_data['is_liked'])
        self.assertEqual(response_data['action'], "liked")
        self.assertIsNotNone(response_data['like_id'])

        # 验证数据库中的记录
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes, 6)

        # 验证Like记录被创建
        like = Like.objects.get(user=self.user2, comment=self.comment)
        self.assertTrue(like.is_active)

    def test_like_same_comment_twice(self):
        """测试重复点赞同一条评论"""
        client = self.get_authenticated_client(self.access_token2)

        # 第一次点赞
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 第二次点赞（应该失败）
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("您已经点赞过该内容", data['message'])

        # 验证点赞数没有重复增加
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes, 6)  # 5 + 1

    def test_like_nonexistent_comment(self):
        """测试点赞不存在的评论"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.post('/api/comments/99999/like/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_like_unauthorized(self):
        """测试未认证用户点赞评论"""
        response = self.client.post(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 401)

    def test_unlike_comment_success(self):
        """测试取消点赞成功"""
        client = self.get_authenticated_client(self.access_token2)

        # 先点赞
        client.post(f'/api/comments/{self.comment.id}/like/')

        # 取消点赞
        response = client.delete(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "取消点赞成功")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.comment.id)
        self.assertEqual(response_data['likes_count'], 5)  # 回到原始值
        self.assertFalse(response_data['is_liked'])
        self.assertEqual(response_data['action'], "unliked")

        # 验证数据库中的记录
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes, 5)

        # 验证Like记录被软删除
        like = Like.objects.get(user=self.user2, comment=self.comment)
        self.assertFalse(like.is_active)

    def test_unlike_never_liked_comment(self):
        """测试取消点赞从未点赞过的评论"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.delete(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("您还未点赞该内容", data['message'])

        # 验证点赞数没有减少
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes, 5)

    def test_unlike_nonexistent_comment(self):
        """测试取消点赞不存在的评论"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.delete('/api/comments/99999/like/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_unlike_unauthorized(self):
        """测试未认证用户取消点赞"""
        response = self.client.delete(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 401)

    def test_get_like_status_liked(self):
        """测试获取点赞状态 - 已点赞"""
        client = self.get_authenticated_client(self.access_token2)

        # 先点赞
        like = Like.objects.create(
            user=self.user2,
            comment=self.comment,
            is_active=True
        )
        self.comment.likes = 6
        self.comment.save()

        response = client.get(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['message'], "success")

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.comment.id)
        self.assertEqual(response_data['likes_count'], 6)
        self.assertTrue(response_data['is_liked'])
        self.assertEqual(response_data['user_like_id'], like.id)

    def test_get_like_status_not_liked(self):
        """测试获取点赞状态 - 未点赞"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.get(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['comment_id'], self.comment.id)
        self.assertEqual(response_data['likes_count'], 5)
        self.assertFalse(response_data['is_liked'])
        self.assertIsNone(response_data['user_like_id'])

    def test_get_like_status_nonexistent_comment(self):
        """测试获取不存在评论的点赞状态"""
        client = self.get_authenticated_client(self.access_token2)

        response = client.get('/api/comments/99999/like/')

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("评论不存在", data['message'])

    def test_get_like_status_unauthorized(self):
        """测试未认证用户获取点赞状态"""
        response = self.client.get(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 401)

    def test_like_workflow_integration(self):
        """测试完整的点赞工作流程"""
        client = self.get_authenticated_client(self.access_token2)

        # 1. 获取初始状态
        response = client.get(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.json()['data']['is_liked'], False)
        self.assertEqual(response.json()['data']['likes_count'], 5)

        # 2. 点赞
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 3. 验证点赞后状态
        response = client.get(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.json()['data']['is_liked'], True)
        self.assertEqual(response.json()['data']['likes_count'], 6)

        # 4. 取消点赞
        response = client.delete(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 5. 验证取消后状态
        response = client.get(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.json()['data']['is_liked'], False)
        self.assertEqual(response.json()['data']['likes_count'], 5)

    def test_multiple_users_like_same_comment(self):
        """测试多个用户点赞同一条评论"""
        # user1 通过 user2 的客户端点赞
        client2 = self.get_authenticated_client(self.access_token2)
        response = client2.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 创建第三个用户并点赞
        user3 = User.objects.create_user(
            username="testuser3",
            email="user3@test.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=user3, cellphone="13800000003")
        refresh_token3 = RefreshToken.for_user(user3)
        access_token3 = str(refresh_token3.access_token)
        client3 = self.get_authenticated_client(access_token3)

        response = client3.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 验证点赞数正确增加
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes, 7)  # 原始5 + user1 + user3

        # 验证两个Like记录都存在且活跃
        self.assertEqual(
            Like.objects.filter(comment=self.comment, is_active=True).count(), 2
        )

    def test_like_after_unlike(self):
        """测试取消点赞后重新点赞"""
        client = self.get_authenticated_client(self.access_token2)

        # 1. 点赞
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 2. 取消点赞
        response = client.delete(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 3. 重新点赞
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 验证最终状态
        response = client.get(f'/api/comments/{self.comment.id}/like/')
        self.assertTrue(response.json()['data']['is_liked'])
        self.assertEqual(response.json()['data']['likes_count'], 6)

        # 修正验证逻辑：应该只有1条记录，状态为活跃
        likes = Like.objects.filter(user=self.user2, comment=self.comment)
        self.assertEqual(likes.count(), 1)  # 唯一约束，只有1条记录
        self.assertEqual(likes.filter(is_active=True).count(), 1)  # 并且是活跃的
    
    def test_like_zero_likes_count(self):
        """测试点赞数为0时的取消点赞"""
        # 创建一条没有点赞的评论
        zero_like_comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=7,
            content="零点赞评论",
            scope='ANIME',
            likes=0
        )

        client = self.get_authenticated_client(self.access_token2)

        # 先点赞
        response = client.post(f'/api/comments/{zero_like_comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 再取消点赞
        response = client.delete(f'/api/comments/{zero_like_comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 验证点赞数不会变成负数
        zero_like_comment.refresh_from_db()
        self.assertEqual(zero_like_comment.likes, 0)

    def test_like_different_comment_types(self):
        """测试对不同类型评论的点赞"""
        # 为user1创建第二条评论
        comment2 = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=9,
            content="第二条评论",
            scope='ANIME',
            likes=3
        )

        client = self.get_authenticated_client(self.access_token2)

        # 点赞第一条评论
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 点赞第二条评论
        response = client.post(f'/api/comments/{comment2.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 验证两条评论都被正确点赞
        self.comment.refresh_from_db()
        comment2.refresh_from_db()
        self.assertEqual(self.comment.likes, 6)  # 5 + 1
        self.assertEqual(comment2.likes, 4)    # 3 + 1

        # 验证用户有两个点赞记录
        self.assertEqual(
            Like.objects.filter(user=self.user2, is_active=True).count(), 2
        )

    @patch('wangumi_app.views.like_view.Comment.save')
    def test_like_database_error(self, mock_save):
        """测试点赞时数据库错误"""
        mock_save.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token2)

        response = client.post(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])

    @patch('wangumi_app.views.like_view.Comment.save')
    def test_unlike_database_error(self, mock_save):
        """测试取消点赞时数据库错误"""
        # 先创建点赞记录
        Like.objects.create(
            user=self.user2,
            comment=self.comment,
            is_active=True
        )
        self.comment.likes = 6
        self.comment.save()

        mock_save.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token2)

        response = client.delete(f'/api/comments/{self.comment.id}/like/')

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])


class LikeViewIntegrationTests(TestCase):
    """点赞系统集成测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="integration_user",
            email="integration@test.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, cellphone="13800000123")

        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

        self.anime = Anime.objects.create(
            title="集成测试番剧",
            title_cn="集成测试番剧中文",
            rating=8.0,
            popularity=100
        )

        self.comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user,
            score=8,
            content="集成测试评论",
            scope='ANIME',
            likes=10
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_concurrent_likes(self):
        """测试并发点赞场景（模拟）"""
        # 这个测试模拟并发场景，虽然在实际测试中不是真正的并发
        client = self.get_authenticated_client(self.access_token)

        # 创建多个用户同时点赞
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@test.com",
                password="testpass123"
            )
            UserProfile.objects.create(user=user, cellphone=f"13800000{i:02d}")
            users.append(user)

        # 逐个点赞（在实际应用中可能是并发的）
        initial_likes = self.comment.likes
        for user in users:
            refresh_token = RefreshToken.for_user(user)
            access_token = str(refresh_token.access_token)
            user_client = self.get_authenticated_client(access_token)

            response = user_client.post(f'/api/comments/{self.comment.id}/like/')
            self.assertEqual(response.status_code, 200)

        # 验证最终点赞数
        self.comment.refresh_from_db()
        expected_likes = initial_likes + len(users)
        self.assertEqual(self.comment.likes, expected_likes)

        # 验证所有Like记录都存在
        self.assertEqual(
            Like.objects.filter(comment=self.comment, is_active=True).count(), len(users)
        )

    def test_like_data_consistency(self):
        """测试点赞数据一致性"""
        client = self.get_authenticated_client(self.access_token)

        # 记录初始状态
        initial_likes = self.comment.likes
        initial_like_count = Like.objects.filter(
            comment=self.comment, is_active=True
        ).count()

        # 点赞
        response = client.post(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 验证数据一致性
        self.comment.refresh_from_db()
        final_like_count = Like.objects.filter(
            comment=self.comment, is_active=True
        ).count()

        self.assertEqual(self.comment.likes, initial_likes + 1)
        self.assertEqual(final_like_count, initial_like_count + 1)
        self.assertEqual(
            self.comment.likes,
            final_like_count + 10  # 10是初始点赞数
        )

        # 取消点赞
        response = client.delete(f'/api/comments/{self.comment.id}/like/')
        self.assertEqual(response.status_code, 200)

        # 再次验证数据一致性
        self.comment.refresh_from_db()
        final_like_count = Like.objects.filter(
            comment=self.comment, is_active=True
        ).count()

        self.assertEqual(self.comment.likes, initial_likes)
        self.assertEqual(final_like_count, initial_like_count)