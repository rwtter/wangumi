"""
测试 anime_delete 和 anime_modify 函数
"""
import json
from unittest.mock import Mock, patch

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import Anime
from wangumi_app.views import anime_views


class AnimeModifyDeleteTestCase(TestCase):
    """测试 anime_modify 和 anime_delete 函数"""

    def setUp(self):
        """设置测试数据"""
        self.factory = RequestFactory()

        # 创建测试用户
        self.normal_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()

        # 创建测试番剧
        self.user_anime = Anime.objects.create(
            title='用户番剧',
            description='用户创建的番剧',
            created_by=self.normal_user,
            is_admin=False
        )

        self.admin_anime = Anime.objects.create(
            title='官方番剧',
            description='官方番剧，仅管理员可操作',
            is_admin=True
        )

        # 创建JWT tokens
        self.normal_user_token = str(RefreshToken.for_user(self.normal_user).access_token)
        self.admin_user_token = str(RefreshToken.for_user(self.admin_user).access_token)

    def create_authenticated_request(self, method, url, user_token, data=None):
        """创建认证的请求"""
        method_func = getattr(self.factory, method.lower())
        request = method_func(
            url,
            data=data,
            content_type='application/json'
        )
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {user_token}'
        return request

    # ==================== anime_delete 测试用例 ====================

    def test_anime_delete_success_by_owner(self):
        """测试：条目创建者成功删除自己的番剧"""
        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/1',
            self.normal_user_token
        )

        response = anime_views.anime_delete(request, self.user_anime.id)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['message'], '条目删除成功')
        self.assertFalse(Anime.objects.filter(id=self.user_anime.id).exists())

    def test_anime_delete_success_by_admin(self):
        """测试：管理员成功删除用户番剧"""
        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/1',
            self.admin_user_token
        )

        response = anime_views.anime_delete(request, self.user_anime.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Anime.objects.filter(id=self.user_anime.id).exists())

    def test_anime_delete_success_admin_anime_by_admin(self):
        """测试：管理员成功删除官方番剧"""
        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/2',
            self.admin_user_token
        )

        response = anime_views.anime_delete(request, self.admin_anime.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Anime.objects.filter(id=self.admin_anime.id).exists())

    def test_anime_delete_no_anime(self):
        """测试：删除不存在的番剧"""
        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/999',
            self.normal_user_token
        )

        response = anime_views.anime_delete(request, 999)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 404)
        self.assertEqual(data['message'], '条目不存在')

    def test_anime_delete_no_authentication(self):
        """测试：未登录用户尝试删除番剧"""
        factory = RequestFactory()
        request = factory.delete('/api/anime/delete/1')

        response = anime_views.anime_delete(request, self.user_anime.id)

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '需要登录才能删除条目')

    def test_anime_delete_user_delete_admin_anime(self):
        """测试：普通用户尝试删除官方番剧"""
        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/2',
            self.normal_user_token
        )

        response = anime_views.anime_delete(request, self.admin_anime.id)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '仅管理员可以删除官方条目')

    def test_anime_delete_user_delete_others_anime(self):
        """测试：用户尝试删除他人创建的番剧"""
        # 创建另一个用户和番剧
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_anime = Anime.objects.create(
            title='他人番剧',
            description='其他人创建的番剧',
            created_by=other_user,
            is_admin=False
        )

        request = self.create_authenticated_request(
            'DELETE',
            '/api/anime/delete/3',
            self.normal_user_token
        )

        response = anime_views.anime_delete(request, other_anime.id)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '无权限删除该条目')

    # ==================== anime_modify 测试用例 ====================

    def test_anime_modify_success_by_owner(self):
        """测试：条目创建者成功修改自己的番剧"""
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '修改后的标题',
            'description': '修改后的描述',
            'cover_url': 'https://example.com/new_cover.jpg'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['message'], '条目修改成功')

        # 验证数据已修改
        updated_anime = Anime.objects.get(id=self.user_anime.id)
        self.assertEqual(updated_anime.title, '修改后的标题')
        self.assertEqual(updated_anime.description, '修改后的描述')
        self.assertEqual(updated_anime.cover_url, 'https://example.com/new_cover.jpg')

    def test_anime_modify_success_by_admin(self):
        """测试：管理员成功修改用户番剧"""
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '管理员修改的标题'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.admin_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 200)
        updated_anime = Anime.objects.get(id=self.user_anime.id)
        self.assertEqual(updated_anime.title, '管理员修改的标题')

    def test_anime_modify_success_admin_anime_by_admin(self):
        """测试：管理员成功修改官方番剧"""
        modify_data = {
            'item_id': str(self.admin_anime.id),
            'description': '管理员修改的官方番剧描述'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.admin_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 200)
        updated_anime = Anime.objects.get(id=self.admin_anime.id)
        self.assertEqual(updated_anime.description, '管理员修改的官方番剧描述')

    def test_anime_modify_partial_update(self):
        """测试：部分字段修改"""
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '仅修改标题'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 200)
        updated_anime = Anime.objects.get(id=self.user_anime.id)
        self.assertEqual(updated_anime.title, '仅修改标题')
        # 其他字段应该保持不变
        self.assertEqual(updated_anime.description, '用户创建的番剧')

    def test_anime_modify_no_modification_data(self):
        """测试：没有提供任何修改内容"""
        modify_data = {
            'item_id': str(self.user_anime.id)
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '没有提供任何修改内容')

    def test_anime_modify_anime_not_exists(self):
        """测试：修改不存在的番剧"""
        modify_data = {
            'item_id': '999',
            'title': '不存在的番剧'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 404)  # 直接返回的 JsonResponse
        self.assertEqual(data['message'], '条目不存在')

    def test_anime_modify_no_authentication(self):
        """测试：未登录用户尝试修改番剧"""
        factory = RequestFactory()
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '未登录修改'
        }
        request = factory.post(
            '/api/edit_item/',
            data=json.dumps(modify_data),
            content_type='application/json'
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '需要登录才能修改条目')

    def test_anime_modify_user_modify_admin_anime(self):
        """测试：普通用户尝试修改官方番剧"""
        modify_data = {
            'item_id': str(self.admin_anime.id),
            'title': '普通用户修改官方番剧'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '仅管理员可以修改官方条目')

    def test_anime_modify_user_modify_others_anime(self):
        """测试：用户尝试修改他人创建的番剧"""
        # 创建另一个用户和番剧
        other_user = User.objects.create_user(
            username='otheruser2',
            email='other2@example.com',
            password='otherpass123'
        )
        other_anime = Anime.objects.create(
            title='他人番剧2',
            description='其他人创建的番剧2',
            created_by=other_user,
            is_admin=False
        )

        modify_data = {
            'item_id': str(other_anime.id),
            'title': '尝试修改他人番剧'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)  # build_error_response 返回 code: 1
        self.assertEqual(data['message'], '无权限修改该条目')

    def test_anime_modify_modified_fields_response(self):
        """测试：响应中包含修改的字段信息"""
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '新标题',
            'description': '新描述',
            'cover_url': 'https://example.com/new_cover.jpg'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['data']['modified_fields'], ['标题', '简介', '封面图片'])
        self.assertIsNotNone(data['data']['updated_at'])

    def test_anime_modify_empty_fields(self):
        """测试：传入空字段的处理"""
        modify_data = {
            'item_id': str(self.user_anime.id),
            'title': '',
            'description': '   ',  # 只有空格
            'cover_url': 'https://example.com/valid_url.jpg'
        }

        request = self.create_authenticated_request(
            'POST',
            '/api/edit_item/',
            self.normal_user_token,
            data=json.dumps(modify_data)
        )

        response = anime_views.anime_modify(request)

        # 只有有效URL会被修改
        self.assertEqual(response.status_code, 200)
        updated_anime = Anime.objects.get(id=self.user_anime.id)
        # 标题和描述应该保持不变（因为是空字符串或只有空格）
        self.assertEqual(updated_anime.title, '用户番剧')
        self.assertEqual(updated_anime.description, '用户创建的番剧')
        self.assertEqual(updated_anime.cover_url, 'https://example.com/valid_url.jpg')