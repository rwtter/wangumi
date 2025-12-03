"""
Tests for user activities API view.
包括用户动态流的测试用例，重点测试隐私设置控制。
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime, timedelta

from wangumi_app.models import (
    UserProfile, UserFollow, Anime, WatchStatus, Comment, Activity, PrivacySetting
)


class UserActivityViewTests(APITestCase):
    """用户动态API测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.friend = User.objects.create_user(username='friend', password='pass123')
        self.stranger = User.objects.create_user(username='stranger', password='pass123')
        self.mutual_user = User.objects.create_user(username='mutual', password='pass123')

        # 创建用户资料
        self.owner_profile = UserProfile.objects.create(user=self.owner)
        self.friend_profile = UserProfile.objects.create(user=self.friend)
        self.stranger_profile = UserProfile.objects.create(user=self.stranger)
        self.mutual_profile = UserProfile.objects.create(user=self.mutual_user)

        # 创建不同的隐私设置
        self.public_privacy = PrivacySetting.objects.create(
            user=self.owner,
            activities='public'
        )
        self.friends_privacy = PrivacySetting.objects.create(
            user=self.friend,
            activities='friends'
        )
        self.self_privacy = PrivacySetting.objects.create(
            user=self.stranger,
            activities='self'
        )
        self.mutual_privacy = PrivacySetting.objects.create(
            user=self.mutual_user,
            activities='mutual'
        )

        # 创建互相关注关系（好友）
        UserFollow.objects.create(follower=self.owner, following=self.friend)
        UserFollow.objects.create(follower=self.friend, following=self.owner)

        # 创建测试 mutual 隐私设置的关注关系：mutual_user 与 owner 互相关注，stranger 只关注 mutual_user
        UserFollow.objects.create(follower=self.owner, following=self.mutual_user)
        UserFollow.objects.create(follower=self.mutual_user, following=self.owner)
        UserFollow.objects.create(follower=self.stranger, following=self.mutual_user)

        # 创建测试番剧
        self.anime = Anime.objects.create(
            title='Test Anime',
            title_cn='测试番剧',
            rating=8.0,
            total_episodes=12
        )

        # 创建动态数据
        self.watch_status = WatchStatus.objects.create(
            user=self.owner,
            anime=self.anime,
            status='WATCHING'
        )

        # 创建评论
        self.comment = Comment.objects.create(
            user=self.owner,
            content_type=ContentType.objects.get_for_model(Anime),
            object_id=self.anime.id,
            score=8,
            content='很好看的番剧'
        )

        # 创建活动记录
        self.activity1 = Activity.objects.create(
            user=self.owner,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=self.watch_status.id,
            action='WATCH'
        )

        self.activity2 = Activity.objects.create(
            user=self.owner,
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.comment.id,
            action='COMMENT'
        )

        # 为其他用户创建一些动态
        self.friend_watch_status = WatchStatus.objects.create(
            user=self.friend,
            anime=self.anime,
            status='FINISHED'
        )

        self.friend_activity = Activity.objects.create(
            user=self.friend,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=self.friend_watch_status.id,
            action='WATCH'
        )

        # 为 mutual_user 创建动态数据
        self.mutual_watch_status = WatchStatus.objects.create(
            user=self.mutual_user,
            anime=self.anime,
            status='FINISHED'
        )

        self.mutual_activity = Activity.objects.create(
            user=self.mutual_user,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=self.mutual_watch_status.id,
            action='WATCH'
        )

        # 生成 tokens
        self.owner_token = str(RefreshToken.for_user(self.owner).access_token)
        self.friend_token = str(RefreshToken.for_user(self.friend).access_token)
        self.stranger_token = str(RefreshToken.for_user(self.stranger).access_token)
        self.mutual_token = str(RefreshToken.for_user(self.mutual_user).access_token)

    def test_public_activities_access(self):
        """测试公开动态的访问权限"""
        url = '/api/user_activities/?user_id=' + str(self.owner.id)

        # 未登录用户访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 陌生人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['data']['pagination']['total'], 2)  # owner有2条动态

        # 好友访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 本人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_friends_activities_access(self):
        """测试好友可见动态的访问权限"""
        url = '/api/user_activities/?user_id=' + str(self.friend.id)

        # 未登录用户访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 陌生人访问 - 确保stranger没有关注friend
        self.assertFalse(UserFollow.objects.filter(follower=self.stranger, following=self.friend).exists())
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('该内容不公开', response.json()['detail'])

        # 好友访问 - 确保owner关注了friend
        self.assertTrue(UserFollow.objects.filter(follower=self.owner, following=self.friend).exists())
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        print(f"Debug: owner accessing friend's activities - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['data']['pagination']['total'], 1)  # friend有1条动态

        # 本人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_self_activities_access(self):
        """测试仅自己可见动态的访问权限"""
        url = '/api/user_activities/?user_id=' + str(self.stranger.id)

        # 未登录用户访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 陌生人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('该内容不公开', response.json()['detail'])

        # 好友访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.friend_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('该内容不公开', response.json()['detail'])

        # 本人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_mutual_activities_access(self):
        """测试互相关注可见动态的访问权限"""
        url = '/api/user_activities/?user_id=' + str(self.mutual_user.id)

        # 未登录用户访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        # 关注但不互相关注的用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.stranger_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('该内容不公开', response.json()['detail'])

        # 互相关注用户访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        print(f"Debug: owner accessing mutual_user's activities - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['data']['pagination']['total'], 1)  # mutual_user有1条动态

        # 本人访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.mutual_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_missing_privacy_setting(self):
        """测试没有隐私设置的用户（应该默认为公开）"""
        new_user = User.objects.create_user(username='newuser', password='pass123')
        UserProfile.objects.create(user=new_user)
        # 不创建PrivacySetting

        # 为新用户创建一些动态
        new_watch_status = WatchStatus.objects.create(
            user=new_user,
            anime=self.anime,
            status='WANT'
        )
        Activity.objects.create(
            user=new_user,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=new_watch_status.id,
            action='WATCH'
        )

        url = '/api/user_activities/?user_id=' + str(new_user.id)

        # 其他用户应该能访问（默认公开）
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_user_not_found(self):
        """测试用户不存在的情况"""
        url = '/api/user_activities/?user_id=99999'

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_missing_user_id(self):
        """测试缺少user_id参数"""
        url = '/api/user_activities/'

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('user_id不能为空', response.json()['message'])

    def test_pagination(self):
        """测试分页功能"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')

        # 测试第一页
        url = f'/api/user_activities/?user_id={self.owner.id}&page=1&limit=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['pagination']['page'], 1)
        self.assertEqual(data['data']['pagination']['limit'], 1)
        self.assertEqual(len(data['data']['list']), 1)
        self.assertEqual(data['data']['pagination']['pages'], 2)

        # 测试第二页
        url = f'/api/user_activities/?user_id={self.owner.id}&page=2&limit=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['pagination']['page'], 2)
        self.assertEqual(len(data['data']['list']), 1)

    def test_invalid_pagination(self):
        """测试无效的分页参数"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')

        # 无效的页码
        url = f'/api/user_activities/?user_id={self.owner.id}&page=0'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('需要是正整数', response.json()['message'])

        # 无效的限制数量
        url = f'/api/user_activities/?user_id={self.owner.id}&limit=-1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('需要是正整数', response.json()['message'])

    def test_delete_activity(self):
        """测试删除动态功能"""
        # 创建一个额外的动态用于删除测试
        test_activity = Activity.objects.create(
            user=self.owner,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=self.watch_status.id,
            action='WATCH'
        )

        url = '/api/user_activities/?activity_id=' + str(test_activity.id)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('动态删除成功', response.json()['message'])

        # 确认动态已被删除
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn('动态不存在或无权限删除', response.json()['message'])

    def test_delete_other_user_activity(self):
        """测试删除其他用户的动态（应该失败）"""
        url = '/api/user_activities/?activity_id=' + str(self.friend_activity.id)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn('动态不存在或无权限删除', response.json()['message'])

    def test_delete_activity_missing_id(self):
        """测试删除动态时缺少activity_id"""
        url = '/api/user_activities/'

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('activity_id不能为空', response.json()['message'])

    def test_activity_response_structure(self):
        """测试动态响应的数据结构"""
        url = '/api/user_activities/?user_id=' + str(self.owner.id)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['code'], 0)
        self.assertIn('data', data)
        self.assertIn('list', data['data'])
        self.assertIn('pagination', data['data'])

        # 检查分页信息
        pagination = data['data']['pagination']
        self.assertIn('page', pagination)
        self.assertIn('limit', pagination)
        self.assertIn('total', pagination)
        self.assertIn('pages', pagination)

        # 检查动态列表结构
        activities = data['data']['list']
        if activities:
            activity = activities[0]
            self.assertIn('id', activity)
            self.assertIn('action', activity)
            self.assertIn('created_at', activity)
            self.assertIn('target_id', activity)
            self.assertIn('target_type', activity)
            self.assertIn('target_title', activity)


class ActivityPrivacyIntegrationTests(APITestCase):
    """动态隐私设置集成测试"""

    def setUp(self):
        """创建测试用户和数据"""
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.viewer = User.objects.create_user(username='viewer', password='pass123')

        # 创建用户资料和隐私设置
        self.profile = UserProfile.objects.create(user=self.owner)
        self.privacy = PrivacySetting.objects.create(
            user=self.owner,
            activities='public'
        )

        # 创建测试数据
        self.anime = Anime.objects.create(title='Test Anime', rating=8.0)
        self.watch_status = WatchStatus.objects.create(
            user=self.owner,
            anime=self.anime,
            status='WATCHING'
        )
        self.activity = Activity.objects.create(
            user=self.owner,
            content_type=ContentType.objects.get_for_model(WatchStatus),
            object_id=self.watch_status.id,
            action='WATCH'
        )

        self.viewer_token = str(RefreshToken.for_user(self.viewer).access_token)

    def test_privacy_setting_change(self):
        """测试动态修改隐私设置后的访问权限变化"""
        url = '/api/user_activities/?user_id=' + str(self.owner.id)

        # 初始为公开，应该能访问
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.viewer_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 修改为仅自己可见
        self.privacy.activities = 'self'
        self.privacy.save()

        # 现在应该不能访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # 修改为好友可见（不是好友，不能访问）
        self.privacy.activities = 'friends'
        self.privacy.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # 创建好友关系
        UserFollow.objects.create(follower=self.owner, following=self.viewer)
        UserFollow.objects.create(follower=self.viewer, following=self.owner)

        # 现在作为好友应该能访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 修改为互相关注可见
        self.privacy.activities = 'mutual'
        self.privacy.save()

        # 现在已经是互相关注，应该能访问
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 创建第三个用户，只关注owner但不互相关注
        follower_only = User.objects.create_user(username='follower_only', password='pass123')
        UserFollow.objects.create(follower=follower_only, following=self.owner)
        follower_token = str(RefreshToken.for_user(follower_only).access_token)

        # 这个用户应该不能访问（因为不是互相关注）
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {follower_token}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)