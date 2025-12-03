"""
追番状态系统测试文件
测试用户对番剧的追番状态设置、获取、删除等功能
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    Anime, WatchStatus, UserProfile
)


class WatchStatusViewTests(TestCase):
    """追番状态功能测试"""

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
        self.anime1 = Anime.objects.create(
            title="测试番剧1",
            title_cn="测试番剧1中文",
            description="这是第一个测试番剧",
            rating=8.5,
            popularity=100
        )

        self.anime2 = Anime.objects.create(
            title="测试番剧2",
            title_cn="测试番剧2中文",
            description="这是第二个测试番剧",
            rating=9.0,
            popularity=200
        )

        self.anime3 = Anime.objects.create(
            title="测试番剧3",
            title_cn="测试番剧3中文",
            description="这是第三个测试番剧",
            rating=7.5,
            popularity=50
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_create_watch_status_want(self):
        """测试创建想看状态"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertIn("追番状态创建成功", data['message'])

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['user_id'], self.user1.id)
        self.assertEqual(response_data['anime_id'], self.anime1.id)
        self.assertEqual(response_data['anime_title'], self.anime1.title)
        self.assertEqual(response_data['status'], "WANT")
        self.assertEqual(response_data['status_display'], "想看")
        self.assertIsNotNone(response_data['id'])
        self.assertIsNotNone(response_data['updated_at'])

        # 验证数据库中的记录
        watch_status = WatchStatus.objects.get(user=self.user1, anime=self.anime1)
        self.assertEqual(watch_status.status, "WANT")

    def test_create_watch_status_watching(self):
        """测试创建在看状态"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WATCHING"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['status_display'], "在看")

    def test_create_watch_status_finished(self):
        """测试创建已看状态"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "FINISHED"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['status_display'], "已看")

    def test_update_existing_watch_status(self):
        """测试更新已有的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        # 先创建一个追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WANT"
        )

        # 更新状态
        watch_data = {
            "anime_id": self.anime1.id,
            "status": "FINISHED"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("追番状态更新成功", data['message'])

        # 验证数据库中的记录已更新
        watch_status = WatchStatus.objects.get(user=self.user1, anime=self.anime1)
        self.assertEqual(watch_status.status, "FINISHED")

    def test_set_watch_status_missing_anime_id(self):
        """测试设置追番状态缺少anime_id"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("anime_id不能为空", data['message'])

    def test_set_watch_status_missing_status(self):
        """测试设置追番状态缺少status"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("status不能为空", data['message'])

    def test_set_watch_status_invalid_status(self):
        """测试设置追番状态使用无效status"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "INVALID_STATUS"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("status值必须是以下之一", data['message'])

        # 验证返回的有效状态列表
        self.assertIn("WANT", data['message'])
        self.assertIn("WATCHING", data['message'])
        self.assertIn("FINISHED", data['message'])

    def test_set_watch_status_nonexistent_anime(self):
        """测试设置不存在番剧的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": 99999,
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("番剧不存在", data['message'])

    def test_set_watch_status_unauthorized(self):
        """测试未认证用户设置追番状态"""
        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response = self.client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_set_watch_status_invalid_json(self):
        """测试发送无效JSON格式"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.post(
            '/api/watch-status/',
            data="invalid json",
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("请求体格式错误", data['message'])

    def test_get_specific_watch_status_exists(self):
        """测试获取特定番剧的追番状态 - 存在"""
        # 创建追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WATCHING"
        )

        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['anime_id'], self.anime1.id)
        self.assertEqual(response_data['anime_title'], self.anime1.title)
        self.assertEqual(response_data['status'], "WATCHING")
        self.assertEqual(response_data['status_display'], "在看")
        self.assertIsNotNone(response_data['updated_at'])

    def test_get_specific_watch_status_not_exists(self):
        """测试获取特定番剧的追番状态 - 不存在"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("未找到追番记录", data['message'])

        # 验证返回的数据
        response_data = data['data']
        self.assertEqual(response_data['anime_id'], self.anime1.id)
        self.assertIsNone(response_data['status'])

    def test_get_specific_watch_status_with_json_body(self):
        """测试通过JSON请求体获取特定番剧的追番状态"""
        # 创建追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="FINISHED"
        )

        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id
        }

        response = client.get(
            '/api/watch-status/',
            data=watch_data,  # 使用查询参数而不是JSON体
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['status'], "FINISHED")

    def test_get_all_watch_statuses_empty(self):
        """测试获取所有追番状态 - 空列表"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/watch-status/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['watch_list'], [])
        self.assertEqual(response_data['total'], 0)

    def test_get_all_watch_statuses_with_data(self):
        """测试获取所有追番状态 - 有数据"""
        # 创建多个追番记录
        now = timezone.now()

        # 创建不同的时间戳以便测试排序
        watch1 = WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WANT",
            updated_at=now - timedelta(days=3)
        )
        watch2 = WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime2,
            status="WATCHING",
            updated_at=now - timedelta(days=1)
        )
        watch3 = WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime3,
            status="FINISHED",
            updated_at=now
        )

        client = self.get_authenticated_client(self.access_token1)
        response = client.get('/api/watch-status/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['total'], 3)
        self.assertEqual(len(response_data['watch_list']), 3)

        # 验证排序（按updated_at倒序）
        watch_list = response_data['watch_list']
        self.assertEqual(watch_list[0]['anime_id'], self.anime3.id)  # 最新
        self.assertEqual(watch_list[1]['anime_id'], self.anime2.id)
        self.assertEqual(watch_list[2]['anime_id'], self.anime1.id)  # 最旧

        # 验证每个记录的内容
        for watch_item in watch_list:
            self.assertIn('anime_id', watch_item)
            self.assertIn('anime_title', watch_item)
            self.assertIn('status', watch_item)
            self.assertIn('status_display', watch_item)
            self.assertIn('updated_at', watch_item)

    def test_get_all_watch_statuses_different_users(self):
        """测试不同用户的追番列表隔离"""
        # user1 的追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WANT"
        )

        # user2 的追番记录
        WatchStatus.objects.create(
            user=self.user2,
            anime=self.anime2,
            status="WATCHING"
        )

        # user1 获取自己的追番列表
        client1 = self.get_authenticated_client(self.access_token1)
        response1 = client1.get('/api/watch-status/')

        self.assertEqual(response1.status_code, 200)
        data1 = response1.json()
        self.assertEqual(data1['data']['total'], 1)
        self.assertEqual(data1['data']['watch_list'][0]['anime_id'], self.anime1.id)

        # user2 获取自己的追番列表
        client2 = self.get_authenticated_client(self.access_token2)
        response2 = client2.get('/api/watch-status/')

        self.assertEqual(response2.status_code, 200)
        data2 = response2.json()
        self.assertEqual(data2['data']['total'], 1)
        self.assertEqual(data2['data']['watch_list'][0]['anime_id'], self.anime2.id)

    def test_get_watch_status_nonexistent_anime(self):
        """测试获取不存在番剧的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/watch-status/', {
            'anime_id': 99999
        })

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("番剧不存在", data['message'])

    def test_get_watch_status_invalid_anime_id(self):
        """测试获取追番状态时anime_id无效"""
        client = self.get_authenticated_client(self.access_token1)

        response = client.get('/api/watch-status/', {
            'anime_id': 'invalid'
        })

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("anime_id必须是整数", data['message'])

    def test_get_watch_status_unauthorized(self):
        """测试未认证用户获取追番状态"""
        response = self.client.get('/api/watch-status/')

        self.assertEqual(response.status_code, 401)

    def test_delete_watch_status_success(self):
        """测试删除追番状态成功"""
        # 创建追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WANT"
        )

        client = self.get_authenticated_client(self.access_token1)

        # 使用 JSON 请求体而不是 URL 参数
        delete_data = {
            "anime_id": self.anime1.id
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 200)
        self.assertIn("追番状态已删除", data['message'])

        # 验证返回数据
        response_data = data['data']
        self.assertEqual(response_data['anime_id'], self.anime1.id)
        self.assertEqual(response_data['anime_title'], self.anime1.title)

        # 验证数据库中的记录被删除
        exists = WatchStatus.objects.filter(user=self.user1, anime=self.anime1).exists()
        self.assertFalse(exists)

    def test_delete_watch_status_with_json_body(self):
        """测试通过JSON请求体删除追番状态"""
        # 创建追番记录
        WatchStatus.objects.create(
            user=self.user1,
            anime=self.anime1,
            status="WANT"
        )

        client = self.get_authenticated_client(self.access_token1)

        delete_data = {
            "anime_id": self.anime1.id
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("追番状态已删除", data['message'])

    def test_delete_nonexistent_watch_status(self):
        """测试删除不存在的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        delete_data = {
            "anime_id": self.anime1.id
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("未找到追番记录", data['message'])

    def test_delete_watch_status_missing_anime_id(self):
        """测试删除追番状态缺少anime_id"""
        client = self.get_authenticated_client(self.access_token1)

        # 发送空的 JSON 请求体
        response = client.delete(
            '/api/watch-status/',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("anime_id参数不能为空", data['message'])

    def test_delete_watch_status_invalid_anime_id(self):
        """测试删除追番状态anime_id无效"""
        client = self.get_authenticated_client(self.access_token1)

        delete_data = {
            "anime_id": "invalid"
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['code'], 400)
        self.assertIn("anime_id必须是整数", data['message'])

    def test_delete_watch_status_nonexistent_anime(self):
        """测试删除不存在番剧的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        delete_data = {
            "anime_id": 99999
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data['code'], 404)
        self.assertIn("番剧不存在", data['message'])

    def test_delete_watch_status_unauthorized(self):
        """测试未认证用户删除追番状态"""
        delete_data = {
            "anime_id": self.anime1.id
        }

        response = self.client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_watch_status_workflow_integration(self):
        """测试完整的追番状态工作流程"""
        client = self.get_authenticated_client(self.access_token1)

        # 1. 创建追番状态
        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 2. 获取追番状态
        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], "WANT")

        # 3. 更新追番状态
        update_data = {
            "anime_id": self.anime1.id,
            "status": "WATCHING"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(update_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 4. 验证更新结果
        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.json()['data']['status'], "WATCHING")

        # 5. 删除追番状态 - 使用 JSON 请求体
        delete_data = {
            "anime_id": self.anime1.id
        }

        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 6. 验证删除结果
        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.status_code, 404)
        
    def test_multiple_watch_statuses_same_user(self):
        """测试同一用户多个番剧的追番状态"""
        client = self.get_authenticated_client(self.access_token1)

        # 为三个番剧设置不同的追番状态
        statuses = [
            {"anime_id": self.anime1.id, "status": "WANT"},
            {"anime_id": self.anime2.id, "status": "WATCHING"},
            {"anime_id": self.anime3.id, "status": "FINISHED"}
        ]

        for status_data in statuses:
            response = client.post(
                '/api/watch-status/',
                data=json.dumps(status_data),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # 验证所有状态都被正确设置
        response = client.get('/api/watch-status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total'], 3)

        # 验证每个番剧的状态
        watch_list = data['data']['watch_list']
        anime_status_map = {item['anime_id']: item['status'] for item in watch_list}

        self.assertEqual(anime_status_map[self.anime1.id], "WANT")
        self.assertEqual(anime_status_map[self.anime2.id], "WATCHING")
        self.assertEqual(anime_status_map[self.anime3.id], "FINISHED")

    def test_same_anime_different_users(self):
        """测试不同用户对同一番剧的追番状态"""
        client1 = self.get_authenticated_client(self.access_token1)
        client2 = self.get_authenticated_client(self.access_token2)

        # user1 设置想看
        watch_data1 = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response1 = client1.post(
            '/api/watch-status/',
            data=json.dumps(watch_data1),
            content_type='application/json'
        )

        self.assertEqual(response1.status_code, 200)

        # user2 设置已看
        watch_data2 = {
            "anime_id": self.anime1.id,
            "status": "FINISHED"
        }

        response2 = client2.post(
            '/api/watch-status/',
            data=json.dumps(watch_data2),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 200)

        # 验证两个用户的状态都独立保存
        response1_get = client1.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })
        self.assertEqual(response1_get.json()['data']['status'], "WANT")

        response2_get = client2.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })
        self.assertEqual(response2_get.json()['data']['status'], "FINISHED")

    @patch('wangumi_app.views.watch_status_view.WatchStatus.objects.update_or_create')
    def test_set_watch_status_database_error(self, mock_update_or_create):
        """测试设置追番状态时数据库错误"""
        mock_update_or_create.side_effect = Exception("数据库连接错误")

        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertEqual(data['code'], 500)
        self.assertIn("服务器内部错误", data['message'])

    @patch('wangumi_app.views.watch_status_view.create_activity')
    def test_watch_status_creates_activity(self, mock_create_activity):
        """测试新增追番状态时创建动态"""
        client = self.get_authenticated_client(self.access_token1)

        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WATCHING"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 验证create_activity被调用
        mock_create_activity.assert_called_once()


class WatchStatusViewIntegrationTests(TestCase):
    """追番状态系统集成测试"""

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

        self.anime1 = Anime.objects.create(
            title="集成测试番剧1",
            title_cn="集成测试番剧1中文",
            rating=8.0,
            popularity=100
        )

        self.anime2 = Anime.objects.create(
            title="集成测试番剧2",
            title_cn="集成测试番剧2中文",
            rating=9.0,
            popularity=200
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_concurrent_watch_status_operations(self):
        """测试并发追番状态操作（模拟）"""
        client = self.get_authenticated_client(self.access_token)

        # 模拟快速连续的操作
        operations = [
            {"anime_id": self.anime1.id, "status": "WANT"},
            {"anime_id": self.anime2.id, "status": "WATCHING"},
            {"anime_id": self.anime1.id, "status": "FINISHED"},  # 更新第一个
        ]

        for operation in operations:
            response = client.post(
                '/api/watch-status/',
                data=json.dumps(operation),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # 删除其中一个追番状态
        delete_data = {
            "anime_id": self.anime2.id
        }
        
        response = client.delete(
            '/api/watch-status/',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # 验证最终状态
        response = client.get('/api/watch-status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total'], 1)  # 只剩一个

        # 验证最终的状态值
        watch_list = data['data']['watch_list']
        status_map = {item['anime_id']: item['status'] for item in watch_list}

        self.assertEqual(status_map[self.anime1.id], "FINISHED")
        # anime2 应该已经被删除    """追番状态系统集成测试"""

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

        self.anime1 = Anime.objects.create(
            title="集成测试番剧1",
            title_cn="集成测试番剧1中文",
            rating=8.0,
            popularity=100
        )

        self.anime2 = Anime.objects.create(
            title="集成测试番剧2",
            title_cn="集成测试番剧2中文",
            rating=9.0,
            popularity=200
        )

    def get_authenticated_client(self, token):
        """获取已认证的客户端"""
        client = Client()
        client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return client

    def test_watch_status_lifecycle_multiple_animes(self):
        """测试多个番剧的追番状态生命周期"""
        client = self.get_authenticated_client(self.access_token)

        animes = [self.anime1, self.anime2]
        status_progression = ["WANT", "WATCHING", "FINISHED"]

        for anime in animes:
            for status in status_progression:
                # 设置状态
                watch_data = {
                    "anime_id": anime.id,
                    "status": status
                }

                response = client.post(
                    '/api/watch-status/',
                    data=json.dumps(watch_data),
                    content_type='application/json'
                )

                self.assertEqual(response.status_code, 200)

                # 验证状态
                response = client.get('/api/watch-status/', {
                    'anime_id': anime.id
                })

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()['data']['status'], status)

        # 验证最终的追番列表
        response = client.get('/api/watch-status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total'], 2)

    def test_watch_status_consistency_after_anime_update(self):
        """测试番剧信息更新后追番状态的一致性"""
        client = self.get_authenticated_client(self.access_token)

        # 设置追番状态
        watch_data = {
            "anime_id": self.anime1.id,
            "status": "WANT"
        }

        response = client.post(
            '/api/watch-status/',
            data=json.dumps(watch_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        # 更新番剧信息
        self.anime1.title = "更新后的番剧标题"
        self.anime1.save()

        # 验证追番状态查询返回最新的番剧信息
        response = client.get('/api/watch-status/', {
            'anime_id': self.anime1.id
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['anime_title'], "更新后的番剧标题")

    def test_concurrent_watch_status_operations(self):
        """测试并发追番状态操作（模拟）"""
        client = self.get_authenticated_client(self.access_token)

        # 模拟快速连续的操作
        operations = [
            {"anime_id": self.anime1.id, "status": "WANT"},
            {"anime_id": self.anime2.id, "status": "WATCHING"},
            {"anime_id": self.anime1.id, "status": "FINISHED"},  # 更新第一个
        ]

        for operation in operations:
            response = client.post(
                '/api/watch-status/',
                data=json.dumps(operation),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # 验证最终状态
        response = client.get('/api/watch-status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['total'], 2)

        # 验证最终的状态值
        watch_list = data['data']['watch_list']
        status_map = {item['anime_id']: item['status'] for item in watch_list}

        self.assertEqual(status_map[self.anime1.id], "FINISHED")
        self.assertEqual(status_map[self.anime2.id], "WATCHING")