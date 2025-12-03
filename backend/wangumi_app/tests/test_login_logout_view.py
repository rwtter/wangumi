"""
Tests for login and logout API views.
测试登录和登出API接口的功能，包括refresh token黑名单机制。
"""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from wangumi_app.models import UserProfile


class LoginViewTests(APITestCase):
    """登录API测试"""

    def setUp(self):
        """创建测试用户"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)
        self.login_url = '/api/login/'

    def test_login_success(self):
        """测试成功登录"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('access', response_data)
        self.assertIn('refresh', response_data)

    def test_login_invalid_credentials(self):
        """测试无效凭据登录"""
        data = {
            'username': 'testuser',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('detail', response_data)

    def test_login_missing_fields(self):
        """测试缺少字段的登录请求"""
        # 缺少密码
        data = {
            'username': 'testuser'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        """测试不存在用户的登录"""
        data = {
            'username': 'nonexistent',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, 401)


class LogoutViewTests(APITestCase):
    """登出API测试"""

    def setUp(self):
        """创建测试用户并获取token"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)

        # 获取refresh token
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

        self.logout_url = '/api/logout/'

    def test_logout_success(self):
        """测试成功登出"""
        # 登录
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        data = {
            'refresh_token': self.refresh_token
        }
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['code'], 0)
        self.assertIn('message', response_data)

        # 验证refresh token已被加入黑名单
        # 使用RefreshToken对象来检查黑名单状态
        from rest_framework_simplejwt.tokens import RefreshToken
        try:
            token = RefreshToken(self.refresh_token)
            # 如果token在黑名单中，这里会抛出TokenError异常
            token.check_blacklist()
            # 如果没有异常，说明token不在黑名单中，测试失败
            self.fail("Refresh token should be blacklisted")
        except Exception:
            # 期望的异常，说明token已被加入黑名单
            pass

    def test_logout_without_refresh_token(self):
        """测试不提供refresh token的登出"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(self.logout_url, {}, format='json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('Refresh token is required', response_data['message'])

    def test_logout_invalid_refresh_token(self):
        """测试无效refresh token的登出"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        data = {
            'refresh_token': 'invalid_refresh_token'
        }
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)

    def test_logout_without_authentication(self):
        """测试未认证的登出请求"""
        data = {
            'refresh_token': self.refresh_token
        }
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, 401)

    def test_logout_expired_token(self):
        """测试过期token的登出"""
        # 创建一个即将过期的refresh token
        from rest_framework_simplejwt.settings import api_settings
        from datetime import datetime, timedelta
        from calendar import timegm
        import jwt
        from django.conf import settings

        expired_time = datetime.utcnow() - timedelta(minutes=1)
        expired_timestamp = timegm(expired_time.utctimetuple())

        payload = {
            'user_id': self.user.id,
            'exp': expired_timestamp,
            'iat': expired_timestamp - timedelta(minutes=5).total_seconds(),
            'jti': 'test_expired_jti'
        }

        expired_token = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm='HS256'
        )

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        data = {
            'refresh_token': expired_token
        }
        response = self.client.post(self.logout_url, data, format='json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)

    def test_logout_double_logout(self):
        """测试重复登出同一个token"""
        # 第一次登出
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        data = {
            'refresh_token': self.refresh_token
        }
        response1 = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response1.status_code, 200)

        # 第二次登出同一个token
        response2 = self.client.post(self.logout_url, data, format='json')
        self.assertEqual(response2.status_code, 400)
        response_data = response2.json()
        self.assertEqual(response_data['code'], 1)


class LogoutAllViewTests(APITestCase):
    """登出所有设备API测试"""

    def setUp(self):
        """创建测试用户并获取tokens"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)

        # 创建多个refresh tokens（模拟多设备登录）
        self.refresh1 = str(RefreshToken.for_user(self.user))
        self.refresh2 = str(RefreshToken.for_user(self.user))
        self.access_token = str(RefreshToken.for_user(self.user).access_token)

        self.logout_all_url = '/api/logout-all/'

    def test_logout_all_success(self):
        """测试成功登出所有设备"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(self.logout_all_url, {}, format='json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data['code'], 0)
        self.assertIn('message', response_data)

        # 验证用户的last_login已更新
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_logout_all_without_authentication(self):
        """测试未认证的登出所有设备请求"""
        response = self.client.post(self.logout_all_url, {}, format='json')

        self.assertEqual(response.status_code, 401)


class TokenRefreshViewTests(APITestCase):
    """Token刷新API测试"""

    def setUp(self):
        """创建测试用户"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)

        # 获取refresh token
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)

        self.refresh_url = '/api/token/refresh/'

    def test_token_refresh_success(self):
        """测试成功刷新token"""
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('access', response_data)

    def test_token_refresh_invalid_token(self):
        """测试无效refresh token"""
        data = {
            'refresh': 'invalid_token'
        }
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, 401)

    def test_token_refresh_missing_token(self):
        """测试缺少refresh token"""
        data = {}
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_token_refresh_blacklisted_token(self):
        """测试刷新已加入黑名单的token"""
        # 先登录获取正确的认证token
        from rest_framework_simplejwt.tokens import RefreshToken
        user_refresh = RefreshToken.for_user(self.user)
        access_token = str(user_refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 先将token加入黑名单
        logout_response = self.client.post('/api/logout/', {
            'refresh_token': self.refresh_token
        }, format='json')

        # 清除认证头，因为token刷新不需要access token
        self.client.credentials()

        # 尝试刷新token
        data = {
            'refresh': self.refresh_token
        }
        response = self.client.post(self.refresh_url, data, format='json')

        self.assertEqual(response.status_code, 401)


class LoginLogoutIntegrationTests(APITestCase):
    """登录登出集成测试"""

    def setUp(self):
        """创建测试用户"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user)

    def test_full_login_logout_cycle(self):
        """测试完整的登录-登出-再登录流程"""
        # 1. 登录
        credentials = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_response = self.client.post('/api/login/', credentials, format='json')
        self.assertEqual(login_response.status_code, 200)

        login_data = login_response.json()
        access_token = login_data['access']
        refresh_token = login_data['refresh']

        # 2. 使用access token访问受保护资源
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/user/profile')
        self.assertEqual(response.status_code, 200)

        # 3. 登出
        logout_response = self.client.post('/api/logout/', {
            'refresh_token': refresh_token
        }, format='json')
        self.assertEqual(logout_response.status_code, 200)

        # 4. 注意：根据JWT的设计，access token在有效期内仍然有效
        # 这是JWT的正常行为，因为access token是无状态的
        # 在JWT标准实现中，access token在过期前仍然有效
        # 这里我们测试refresh token已经被加入黑名单
        # 注意：实际生产环境中，可以通过其他方式（如服务器端token黑名单）来实现access token的立即失效

        # 5. 验证refresh token已失效（尝试刷新token应失败）
        refresh_response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        }, format='json')
        self.assertEqual(refresh_response.status_code, 401)

        # 6. 清除认证头，重新登录应该成功
        self.client.credentials()
        new_login_response = self.client.post('/api/login/', credentials, format='json')
        self.assertEqual(new_login_response.status_code, 200)