"""
评论系统测试文件 - 修复版本
测试评论的创建、获取、更新等功能，包括番剧、剧集、角色、人物、条目等多种评论类型
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    Anime, Episode, Comment, Like, WatchStatus,
    Character, Person, UserProfile
)


class CommentViewTests(TestCase):
    """评论功能测试"""

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
            popularity=100,
            genres=["Action", "Comedy"],
            status="FINISHED",
            total_episodes=12
        )

        # 创建测试剧集
        self.episode = Episode.objects.create(
            anime=self.anime,
            episode_number=1,
            title="第一集",
            title_cn="第一集中文",
            description="第一集内容"
        )

        # 创建测试角色
        self.character = Character.objects.create(
            name="测试角色",
            image="character.jpg"
        )

        # 创建测试人物
        self.person = Person.objects.create(
            pers_name="测试人物",
            pers_type=1,
            summary="测试人物简介",
            pers_img="person.jpg"
        )

        # 创建用户自建条目
        self.user_item = Anime.objects.create(
            title="用户自建条目",
            title_cn="用户自建条目中文",
            description="用户创建的条目",
            rating=7.5,
            popularity=50,
            is_admin=False,  # 用户自建
            created_by=self.user1
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_get_anime_comments_success(self):
        """测试获取番剧评论成功"""
        # 创建测试评论
        comment1 = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=8,
            content="很好看的番剧",
            scope='ANIME'
        )
        comment2 = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user2,
            score=9,
            content="非常精彩",
            scope='ANIME'
        )

        # 发起请求
        response = self.client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['data']['scope'], 'ANIME')
        self.assertEqual(data['data']['object_id'], str(self.anime.id))
        self.assertEqual(len(data['data']['comments']), 2)
        self.assertEqual(data['data']['total_comments'], 2)

        # 验证评论数据
        comments = data['data']['comments']
        self.assertEqual(comments[0]['score'], 9)  # 按时间倒序
        self.assertEqual(comments[1]['score'], 8)

    def test_get_anime_comments_authenticated(self):
        """测试认证用户获取番剧评论"""
        # 创建测试评论
        comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=8,
            content="很好看的番剧",
            scope='ANIME'
        )

        # 使用认证客户端
        client = self.get_authenticated_client(self.access_token2)
        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

    def test_create_anime_comment_success(self):
        """测试创建番剧评论成功"""
        client = self.get_authenticated_client(self.access_token1)

        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 8,
            "content": "这是一部非常优秀的番剧！"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 201)
        self.assertEqual(data['message'], "评论发表成功")
        self.assertEqual(data['data']['score'], 8)  # 修正：存储为整数
        self.assertEqual(data['data']['content'], "这是一部非常优秀的番剧！")

        # 验证数据库中创建了评论
        comment = Comment.objects.get(user=self.user1, scope='ANIME')
        self.assertEqual(comment.score, 8)  # 存储为整数
        self.assertEqual(comment.content, "这是一部非常优秀的番剧！")

    def test_create_comment_validation_errors(self):
        """测试创建评论参数验证错误"""
        client = self.get_authenticated_client(self.access_token1)

        # 测试无效评分
        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 15.0,  # 超出范围
            "content": "评分无效的评论"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        # 修正：返回的是参数错误格式
        self.assertIn("请求参数错误", data['message'])

    def test_create_comment_empty_content(self):
        """测试创建评论内容为空"""
        client = self.get_authenticated_client(self.access_token1)

        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 8.0,
            "content": ""  # 空内容
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        # 修正：返回的是参数错误格式
        self.assertIn("请求参数错误", data['message'])

    def test_put_update_comment_success(self):
        """测试PUT方法更新评论成功"""
        client = self.get_authenticated_client(self.access_token1)

        # 创建评论
        comment = Comment.objects.create(
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            user=self.user1,
            score=7,
            content="原始评论",
            scope='ANIME'
        )

        # 使用PUT方法更新
        update_data = {
            "comment_id": comment.id,
            "score": 8,  # 修正：使用整数
            "content": "PUT方法更新的评论"
        }

        response = client.put(
            '/api/comments/',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertEqual(data['data']['comment_id'], comment.id)
        self.assertEqual(data['data']['score'], 8)  # 修正：期望整数

    def test_create_episode_comment_success(self):
        """测试创建剧集评论成功"""
        client = self.get_authenticated_client(self.access_token1)

        comment_data = {
            "scope": "EPISODE",
            "object_id": self.episode.id,
            "score": 7,
            "content": "这一集很有趣"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['code'], 201)
        self.assertEqual(data['data']['scope'], 'EPISODE')

    def test_get_comments_pagination(self):
        """测试评论分页功能"""
        # 创建多条评论
        for i in range(5):
            Comment.objects.create(
                content_type=ContentType.objects.get_for_model(Anime),
                object_id=self.anime.id,
                user=self.user1 if i % 2 == 0 else self.user2,
                score=7 + i,
                content=f"评论{i+1}",
                scope='ANIME'
            )

        # 使用认证客户端进行分页测试
        client = self.get_authenticated_client(self.access_token1)
        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id,
            'page': 1,
            'page_size': 2
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['data']['comments']), 2)
        self.assertEqual(data['data']['page'], 1)
        self.assertEqual(data['data']['page_size'], 2)
        self.assertEqual(data['data']['total_pages'], 3)
        self.assertEqual(data['data']['total_comments'], 5)

    def test_get_comments_missing_parameters(self):
        """测试获取评论缺少参数"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/comments/', {
            'scope': 'ANIME'
            # 缺少 object_id
        })

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("scope和object_id参数不能为空", data['message'])

    def test_get_nonexistent_object_comments(self):
        """测试获取不存在对象的评论"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': 99999  # 不存在的番剧ID
        })

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("番剧不存在", data['message'])

    def test_comment_workflow_integration(self):
        """测试完整的评论工作流程"""
        client = self.get_authenticated_client(self.access_token1)

        # 1. 创建评论
        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 8,
            "content": "首次评论"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        comment_id = response.json()['data']['comment_id']

        # 2. 获取评论列表
        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']['comments']), 1)

        # 3. 更新评论
        update_data = {
            "comment_id": comment_id,
            "score": 9,
            "content": "更新后的评论"
        }

        response = client.put(
            '/api/comments/',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 4. 验证更新结果
        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id
        })

        comments = response.json()['data']['comments']
        self.assertEqual(comments[0]['score'], 9)
        self.assertEqual(comments[0]['content'], "更新后的评论")

    @patch('wangumi_app.views.comments_view.CommentView._increase_heat')
    def test_comment_increases_heat(self, mock_increase_heat):
        """测试评论增加热度"""
        mock_increase_heat.return_value = True

        client = self.get_authenticated_client(self.access_token1)

        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 8,
            "content": "新评论"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['data']['heat_increased'])
        mock_increase_heat.assert_called_once()


class CommentIntegrationTests(TestCase):
    """评论系统集成测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, cellphone="13800000000")

        self.refresh_token = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh_token.access_token)

        self.anime = Anime.objects.create(
            title="集成测试番剧",
            title_cn="集成测试番剧中文",
            rating=8.0,
            popularity=100
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_comment_workflow_complete(self):
        """测试完整的评论工作流程"""
        client = self.get_authenticated_client(self.access_token)

        # 1. 创建评论
        comment_data = {
            "scope": "ANIME",
            "object_id": self.anime.id,
            "score": 8,
            "content": "工作流程评论"
        }

        response = client.post(
            '/api/comments/',
            data=json.dumps(comment_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 2. 获取评论列表
        response = client.get('/api/comments/', {
            'scope': 'ANIME',
            'object_id': self.anime.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['data']['comments']), 1)

        # 3. 验证评论内容
        comments = response.json()['data']['comments']
        self.assertEqual(comments[0]['content'], "工作流程评论")
        self.assertEqual(comments[0]['score'], 8)