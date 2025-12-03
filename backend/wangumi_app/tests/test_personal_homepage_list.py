"""
Tests for user homepage list API views.
包括关注列表、粉丝列表、番剧列表的测试用例。
"""

from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    UserProfile, UserFollow, Anime, WatchStatus, PrivacySetting
)


class UserFollowingListViewTests(APITestCase):
    """用户关注列表API测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user3 = User.objects.create_user(username='user3', password='pass123')
        self.user4 = User.objects.create_user(username='user4', password='pass123')
        self.user5 = User.objects.create_user(username='user5', password='pass123')

        # 创建用户资料
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.profile3 = UserProfile.objects.create(user=self.user3)
        self.profile4 = UserProfile.objects.create(user=self.user4)
        self.profile5 = UserProfile.objects.create(user=self.user5)

        # 创建隐私设置
        self.privacy1 = PrivacySetting.objects.create(user=self.user1, followings='public')
        self.privacy2 = PrivacySetting.objects.create(user=self.user2, followings='public')
        self.privacy3 = PrivacySetting.objects.create(user=self.user3, followings='friends')
        self.privacy4 = PrivacySetting.objects.create(user=self.user4, followings='self')
        self.privacy5 = PrivacySetting.objects.create(user=self.user5, followings='mutual')

        # 创建关注关系：user1 关注 user2, user3
        UserFollow.objects.create(follower=self.user1, following=self.user2)
        UserFollow.objects.create(follower=self.user1, following=self.user3)

        # 创建互相关注关系：user2 和 user3 互相关注（用于测试好友权限）
        UserFollow.objects.create(follower=self.user2, following=self.user3)
        UserFollow.objects.create(follower=self.user3, following=self.user2)

        # 创建测试 mutual 隐私设置的关注关系：user5 与 user1 互相关注
        UserFollow.objects.create(follower=self.user1, following=self.user5)
        UserFollow.objects.create(follower=self.user5, following=self.user1)
        # 但 user5 不关注 user3（测试 friends vs mutual 的区别）
        UserFollow.objects.create(follower=self.user3, following=self.user5)

        # 生成 JWT token
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)

    def test_following_list_public_access(self):
        """测试公开关注列表的访问"""
        url = f'/api/personal_homepage_following_list/{self.user1.id}'

        # 测试未登录访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 测试已登录访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 3)

        # 验证返回数据结构
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('username', result)
        self.assertIn('avatar', result)
        self.assertIn('followed_at', result)

    def test_following_list_pagination(self):
        """测试关注列表分页"""
        url = f'/api/personal_homepage_following_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 测试第一页
        response = self.client.get(url, {'page': 1, 'limit': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['total_pages'], 2)

        # 测试第二页
        response = self.client.get(url, {'page': 2, 'limit': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['page'], 2)
        self.assertEqual(len(data['results']), 1)

    def test_following_list_privacy_self(self):
        """测试 privacy='self' 的隐私控制"""
        url = f'/api/personal_homepage_following_list/{self.user4.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 其他用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的关注列表不公开', response_data['message'])

        # 本人访问
        refresh = RefreshToken.for_user(self.user4)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_following_list_privacy_friends(self):
        """测试 privacy='friends' 的隐私控制"""
        url = f'/api/personal_homepage_following_list/{self.user3.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非互关用户访问（user1 与 user3 未互关，但是user1关注了user3 ）
        refresh = RefreshToken.for_user(self.user1)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 好友用户访问（user2 是 user3 的好友）
        refresh = RefreshToken.for_user(self.user2)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_following_list_invalid_pagination(self):
        """测试无效的分页参数"""
        url = f'/api/personal_homepage_following_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 无效的页码
        response = self.client.get(url, {'page': 0})
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('正整数', response_data['message'])

        # 无效的限制数量
        response = self.client.get(url, {'limit': -1})
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('正整数', response_data['message'])

        # 非数字参数
        response = self.client.get(url, {'page': 'abc'})
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('正整数', response_data['message'])

    def test_following_list_privacy_mutual(self):
        """测试 privacy='mutual' 的隐私控制"""
        url = f'/api/personal_homepage_following_list/{self.user5.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非互相关注用户访问（user3 关注 user5 但 user5 没有关注 user3）
        refresh = RefreshToken.for_user(self.user3)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的关注列表不公开', response_data['message'])

        # 互相关注用户访问（user1 和 user5 互相关注）
        refresh = RefreshToken.for_user(self.user1)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人访问
        refresh = RefreshToken.for_user(self.user5)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class UserFollowerListViewTests(APITestCase):
    """用户粉丝列表API测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user3 = User.objects.create_user(username='user3', password='pass123')
        self.user4 = User.objects.create_user(username='user4', password='pass123')
        self.user5 = User.objects.create_user(username='user5', password='pass123')

        # 创建用户资料
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.profile3 = UserProfile.objects.create(user=self.user3)
        self.profile5 = UserProfile.objects.create(user=self.user5)

        # 创建隐私设置
        self.privacy1 = PrivacySetting.objects.create(user=self.user1, followers='public')
        self.privacy2 = PrivacySetting.objects.create(user=self.user2, followers='friends')
        self.privacy3 = PrivacySetting.objects.create(user=self.user3, followers='self')
        self.privacy5 = PrivacySetting.objects.create(user=self.user5, followers='mutual')

        # 创建粉丝关系：user2, user3, user4 都关注 user1
        UserFollow.objects.create(follower=self.user2, following=self.user1)
        UserFollow.objects.create(follower=self.user3, following=self.user1)
        UserFollow.objects.create(follower=self.user4, following=self.user1)

        # 创建互相关注关系：user1 和 user2 互相关注（用于测试好友权限）
        UserFollow.objects.create(follower=self.user1, following=self.user2)

        # 创建测试 mutual 隐私设置的粉丝关系：user5 与 user1 互相关注，user3 也关注 user5
        UserFollow.objects.create(follower=self.user3, following=self.user5)
        UserFollow.objects.create(follower=self.user5, following=self.user1)
        UserFollow.objects.create(follower=self.user1, following=self.user5)

        # 生成 JWT token
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)

    def test_follower_list_public_access(self):
        """测试公开粉丝列表的访问"""
        url = f'/api/personal_homepage_follower_list/{self.user1.id}'

        # 测试未登录访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 测试已登录访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 4)
        self.assertEqual(len(data['results']), 4)

        # 验证返回数据结构
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('username', result)
        self.assertIn('avatar', result)
        self.assertIn('followed_at', result)

    def test_follower_list_pagination(self):
        """测试粉丝列表分页"""
        url = f'/api/personal_homepage_follower_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(url, {'page': 1, 'limit': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['total_pages'], 2)

    def test_follower_list_privacy_self(self):
        """测试 privacy='self' 的隐私控制"""
        url = f'/api/personal_homepage_follower_list/{self.user3.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 其他用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的粉丝列表不公开', response_data['message'])

        # 本人访问
        refresh = RefreshToken.for_user(self.user3)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_follower_list_privacy_friends(self):
        """测试 privacy='friends' 的隐私控制"""
        url = f'/api/personal_homepage_follower_list/{self.user2.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非好友用户访问（假设 user3 不是 user2 的好友）
        refresh = RefreshToken.for_user(self.user3)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的粉丝列表不公开', response_data['message'])

        # 好友用户访问（user1 是 user2 的好友）
        refresh = RefreshToken.for_user(self.user1)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_follower_list_privacy_mutual(self):
        """测试 privacy='mutual' 的隐私控制"""
        url = f'/api/personal_homepage_follower_list/{self.user5.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非互相关注用户访问（user3 关注 user5 但 user5 没有关注 user3）
        refresh = RefreshToken.for_user(self.user3)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的粉丝列表不公开', response_data['message'])

        # 互相关注用户访问（user1 和 user5 互相关注）
        refresh = RefreshToken.for_user(self.user1)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人访问
        refresh = RefreshToken.for_user(self.user5)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class UserAnimeListViewTests(APITestCase):
    """用户番剧列表API测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user3 = User.objects.create_user(username='user3', password='pass123')
        self.user4 = User.objects.create_user(username='user4', password='pass123')

        # 创建用户资料
        self.profile1 = UserProfile.objects.create(user=self.user1)
        self.profile2 = UserProfile.objects.create(user=self.user2)
        self.profile3 = UserProfile.objects.create(user=self.user3)
        self.profile4 = UserProfile.objects.create(user=self.user4)

        # 创建隐私设置，使用watchlist字段
        self.privacy1 = PrivacySetting.objects.create(user=self.user1, watchlist='public')
        self.privacy2 = PrivacySetting.objects.create(user=self.user2, watchlist='friends')
        self.privacy3 = PrivacySetting.objects.create(user=self.user3, watchlist='self')
        self.privacy4 = PrivacySetting.objects.create(user=self.user4, watchlist='mutual')

        # 创建番剧
        self.anime1 = Anime.objects.create(
            title='Anime 1',
            title_cn='番剧1',
            rating=8.5,
            cover_url='https://example.com/cover1.jpg',
            total_episodes=12,
            genres=['Action', 'Comedy']
        )
        self.anime2 = Anime.objects.create(
            title='Anime 2',
            title_cn='番剧2',
            rating=9.0,
            cover_image='path/to/cover2.jpg',
            total_episodes=24,
            genres=['Drama']
        )
        self.anime3 = Anime.objects.create(
            title='Anime 3',
            title_cn='番剧3',
            rating=7.5,
            total_episodes=6,
            genres=['Romance']
        )

        # 创建追番记录
        WatchStatus.objects.create(user=self.user1, anime=self.anime1, status='WATCHING')
        WatchStatus.objects.create(user=self.user1, anime=self.anime2, status='FINISHED')
        WatchStatus.objects.create(user=self.user1, anime=self.anime3, status='WANT')

        WatchStatus.objects.create(user=self.user2, anime=self.anime1, status='WATCHING')
        WatchStatus.objects.create(user=self.user4, anime=self.anime2, status='WATCHING')

        # 创建测试 mutual 隐私设置的关注关系：user4 与 user1 互相关注，user2 只关注 user4
        UserFollow.objects.create(follower=self.user1, following=self.user4)
        UserFollow.objects.create(follower=self.user4, following=self.user1)
        UserFollow.objects.create(follower=self.user2, following=self.user4)

        # 生成 JWT token
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)

    def test_anime_list_public_access(self):
        """测试公开番剧列表的访问"""
        url = f'/api/personal_homepage_anime_list/{self.user1.id}'

        # 测试未登录访问 - 现在需要认证，应该返回401
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 测试已登录访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 3)
        self.assertEqual(len(data['results']), 3)

        # 验证返回数据结构 - 根据实际API返回的字段
        result = data['results'][0]
        self.assertIn('id', result)
        self.assertIn('title', result)
        self.assertIn('title_cn', result)
        self.assertIn('cover', result)
        self.assertIn('rating', result)
        self.assertIn('status', result)
        self.assertIn('status_display', result)

    def test_anime_list_pagination(self):
        """测试番剧列表分页"""
        url = f'/api/personal_homepage_anime_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(url, {'page': 1, 'limit': 2})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 2)
        self.assertEqual(len(data['results']), 2)
        self.assertEqual(data['total_pages'], 2)

    def test_anime_list_status_filter(self):
        """测试按状态筛选番剧列表"""
        url = f'/api/personal_homepage_anime_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 筛选在看状态的番剧
        response = self.client.get(url, {'status': 'WATCHING'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'WATCHING')

        # 筛选已看完的番剧
        response = self.client.get(url, {'status': 'FINISHED'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['status'], 'FINISHED')

    def test_anime_list_invalid_status_filter(self):
        """测试无效的状态筛选参数"""
        url = f'/api/personal_homepage_anime_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        response = self.client.get(url, {'status': 'INVALID'})
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('无效的状态参数', response_data['message'])

    def test_anime_list_privacy_self(self):
        """测试 privacy='self' 的隐私控制"""
        url = f'/api/personal_homepage_anime_list/{self.user3.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 其他用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 本人访问
        refresh = RefreshToken.for_user(self.user3)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_anime_list_privacy_friends(self):
        """测试 privacy='friends' 的隐私控制"""
        url = f'/api/personal_homepage_anime_list/{self.user2.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非好友用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

    def test_anime_list_cover_url_priority(self):
        """测试封面URL的解析逻辑（使用anime_views中的_resolve_cover_url函数）"""
        url = f'/api/personal_homepage_anime_list/{self.user1.id}'

        # 需要认证才能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # anime1 有 cover_url，应该返回 cover_url
        anime1_result = next(r for r in data['results'] if r['id'] == self.anime1.id)
        self.assertEqual(anime1_result['cover'], self.anime1.cover_url)

        # anime2 只有 cover_image，应该返回 cover_image 的 URL 或空字符串
        anime2_result = next(r for r in data['results'] if r['id'] == self.anime2.id)
        # 由于测试环境中可能没有真实的媒体文件，可能是空字符串或路径
        self.assertIsInstance(anime2_result['cover'], str)

    def test_anime_list_privacy_mutual(self):
        """测试 privacy='mutual' 的隐私控制"""
        url = f'/api/personal_homepage_anime_list/{self.user4.id}'

        # 未登录用户访问 - 应该返回401因为需要认证
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 非互相关注用户访问（user2 关注 user4 但 user4 没有关注 user2）
        refresh = RefreshToken.for_user(self.user2)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 互相关注用户访问（user1 和 user4 互相关注）
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人访问
        refresh = RefreshToken.for_user(self.user4)
        token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class PrivacyAnimeFieldTests(APITestCase):
    """专门测试privacy_anime字段的测试类"""

    def setUp(self):
        """创建测试用户和数据"""
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.friend = User.objects.create_user(username='friend', password='pass123')
        self.stranger = User.objects.create_user(username='stranger', password='pass123')
        self.mutual_user = User.objects.create_user(username='mutual', password='pass123')

        # 设置不同的隐私级别
        self.owner_profile = UserProfile.objects.create(user=self.owner)
        self.friend_profile = UserProfile.objects.create(user=self.friend)
        self.stranger_profile = UserProfile.objects.create(user=self.stranger)
        self.mutual_profile = UserProfile.objects.create(user=self.mutual_user)

        # 创建隐私设置
        self.owner_privacy = PrivacySetting.objects.create(
            user=self.owner,
            watchlist='public'  # 公开番剧列表
        )

        self.friend_privacy = PrivacySetting.objects.create(
            user=self.friend,
            watchlist='friends'  # 好友可见番剧列表
        )

        self.stranger_privacy = PrivacySetting.objects.create(
            user=self.stranger,
            watchlist='self'  # 仅自己可见番剧列表
        )

        self.mutual_privacy = PrivacySetting.objects.create(
            user=self.mutual_user,
            watchlist='mutual'  # 互相关注可见番剧列表
        )

        # 创建互相关注关系（好友）
        UserFollow.objects.create(follower=self.owner, following=self.friend)
        UserFollow.objects.create(follower=self.friend, following=self.owner)

        # 创建测试 mutual 隐私设置的关注关系：mutual_user 与 owner 互相关注，stranger 只关注 mutual_user
        UserFollow.objects.create(follower=self.owner, following=self.mutual_user)
        UserFollow.objects.create(follower=self.mutual_user, following=self.owner)
        UserFollow.objects.create(follower=self.stranger, following=self.mutual_user)

        # 创建测试番剧和追番记录
        self.anime = Anime.objects.create(
            title='Test Anime',
            title_cn='测试番剧',
            rating=8.0,
            total_episodes=12,
            genres=['Action', 'Comedy']
        )

        # 为每个用户创建追番记录
        WatchStatus.objects.create(user=self.owner, anime=self.anime, status='WATCHING')
        WatchStatus.objects.create(user=self.friend, anime=self.anime, status='FINISHED')
        WatchStatus.objects.create(user=self.stranger, anime=self.anime, status='WANT')
        WatchStatus.objects.create(user=self.mutual_user, anime=self.anime, status='WATCHING')

        # 生成 tokens
        self.owner_token = str(RefreshToken.for_user(self.owner).access_token)
        self.friend_token = str(RefreshToken.for_user(self.friend).access_token)
        self.stranger_token = str(RefreshToken.for_user(self.stranger).access_token)
        self.mutual_token = str(RefreshToken.for_user(self.mutual_user).access_token)

    def test_privacy_anime_public_access(self):
        """测试privacy_anime='public'的访问权限"""
        url = f'/api/personal_homepage_anime_list/{self.owner.id}'

        # 未登录用户不应该能访问（需要认证）
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 其他用户应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

        # 好友应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_privacy_anime_friends_access(self):
        """测试privacy_anime='friends'的访问权限"""
        url = f'/api/personal_homepage_anime_list/{self.friend.id}'

        # 未登录用户不应该能访问（需要认证）
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 陌生人不应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 好友应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_privacy_anime_self_access(self):
        """测试privacy_anime='self'的访问权限"""
        url = f'/api/personal_homepage_anime_list/{self.stranger.id}'

        # 未登录用户不应该能访问（需要认证）
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 其他用户不应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 好友也不应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 本人应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_privacy_watchlist_mutual_access(self):
        """测试privacy_watchlist='mutual'的访问权限"""
        url = f'/api/personal_homepage_anime_list/{self.mutual_user.id}'

        # 未登录用户不应该能访问（需要认证）
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 关注但不互相关注的用户不应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 互相关注用户应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.mutual_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 1)

    def test_privacy_watchlist_default_value(self):
        """测试watchlist字段的默认值"""
        new_user = User.objects.create_user(username='newuser', password='pass123')
        profile = UserProfile.objects.create(user=new_user)
        privacy = PrivacySetting.objects.create(user=new_user)

        # 检查默认值是否为'public'
        self.assertEqual(privacy.watchlist, 'public')


class PrivacyIntegrationTests(APITestCase):
    """隐私设置集成测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.friend = User.objects.create_user(username='friend', password='pass123')
        self.stranger = User.objects.create_user(username='stranger', password='pass123')

        # 设置不同的隐私级别
        self.owner_profile = UserProfile.objects.create(
            user=self.owner
        )
        self.friend_profile = UserProfile.objects.create(
            user=self.friend
        )

        # 创建隐私设置
        self.owner_privacy = PrivacySetting.objects.create(
            user=self.owner,
            followings='friends',
            followers='friends',
            activities='self',
            watchlist='self',
        )

        self.friend_privacy = PrivacySetting.objects.create(
            user=self.friend,
            followings='public',
            followers='public',
            activities='public',
            watchlist='friends',
        )

        # 创建互相关注关系（好友）
        UserFollow.objects.create(follower=self.owner, following=self.friend)
        UserFollow.objects.create(follower=self.friend, following=self.owner)

        # 创建测试数据
        self.anime = Anime.objects.create(title='Test Anime', rating=8.0)
        WatchStatus.objects.create(user=self.owner, anime=self.anime, status='WATCHING')
        # 注释掉这行，让stranger不是owner的关注对象，这样stranger就无法访问friends隐私的内容
        # UserFollow.objects.create(follower=self.owner, following=self.stranger)

        # 生成 tokens
        self.owner_token = str(RefreshToken.for_user(self.owner).access_token)
        self.friend_token = str(RefreshToken.for_user(self.friend).access_token)
        self.stranger_token = str(RefreshToken.for_user(self.stranger).access_token)

    def test_comprehensive_privacy_control(self):
        """测试综合隐私控制"""
        base_url_following = f'/api/personal_homepage_following_list/{self.owner.id}'
        base_url_followers = f'/api/personal_homepage_follower_list/{self.owner.id}'
        base_url_anime = f'/api/personal_homepage_anime_list/{self.owner.id}'

        # 测试未登录用户 - 现在所有都需要认证，应该返回401
        for url in [base_url_following, base_url_followers, base_url_anime]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 401)

        # 测试陌生人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')

        # 测试关注列表
        response = self.client.get(base_url_following)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的关注列表不公开', response_data['message'])

        # 测试粉丝列表
        response = self.client.get(base_url_followers)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的粉丝列表不公开', response_data['message'])

        response = self.client.get(base_url_anime)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 测试好友访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        for url in [base_url_following, base_url_followers]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

        response = self.client.get(base_url_anime)
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['code'], 1)
        self.assertIn('该用户的番剧列表不公开', response_data['message'])

        # 测试本人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        for url in [base_url_following, base_url_followers, base_url_anime]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


class ErrorHandlingTests(APITestCase):
    """错误处理测试"""

    def setUp(self):
        """创建测试用户"""
        self.user = User.objects.create_user(username='testuser', password='pass123')
        profile = UserProfile.objects.create(user=self.user)
        PrivacySetting.objects.create(user=self.user)

    def test_user_not_found(self):
        """测试用户不存在的情况"""
        urls = [
            '/api/personal_homepage_following_list/999',
            '/api/personal_homepage_follower_list/999',
            '/api/personal_homepage_anime_list/999'
        ]

        for url in urls:
            response = self.client.get(url)
            # 由于需要认证，未登录访问应该返回401而不是404
            self.assertEqual(response.status_code, 401)

    def test_user_profile_not_found(self):
        """测试用户资料不存在的情况"""
        user_no_profile = User.objects.create_user(username='noprofile', password='pass123')

        urls = [
            f'/api/personal_homepage_following_list/{user_no_profile.id}',
            f'/api/personal_homepage_follower_list/{user_no_profile.id}',
            f'/api/personal_homepage_anime_list/{user_no_profile.id}'
        ]

        for url in urls:
            response = self.client.get(url)
            # 由于需要认证，未登录访问应该返回401而不是404
            self.assertEqual(response.status_code, 401)