from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import UserFollow, WatchStatus, Anime

User = get_user_model()


class UserRecommendationTests(TestCase):
    def setUp(self):
        # 创建用户
        self.user = User.objects.create_user(username="A", password="123")
        self.u1 = User.objects.create_user(username="B", password="123")
        self.u2 = User.objects.create_user(username="C", password="123")
        self.u3 = User.objects.create_user(username="D", password="123")

        # 创建番剧
        self.a1 = Anime.objects.create(title="a1", title_cn="a1")
        self.a2 = Anime.objects.create(title="a2", title_cn="a2")
        self.a3 = Anime.objects.create(title="a3", title_cn="a3")

        # A 追番 a1, a2（修正状态值为 WATCHING）
        WatchStatus.objects.create(user=self.user, anime=self.a1, status="WATCHING")
        WatchStatus.objects.create(user=self.user, anime=self.a2, status="WATCHING")

        # B 追番 a1（共同1部）
        WatchStatus.objects.create(user=self.u1, anime=self.a1, status="WATCHING")

        # C 追番 a1, a2（共同2部）
        WatchStatus.objects.create(user=self.u2, anime=self.a1, status="WATCHING")
        WatchStatus.objects.create(user=self.u2, anime=self.a2, status="WATCHING")

        # D 不追番（共同0部）
        # 不创建任何 WatchStatus

    def _auth(self, user):
        """生成认证 token"""
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

    def test_recommendation_basic(self):
        """测试基本推荐功能"""
        url = "/api/recommend_users/"
        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertIn("results", data)
        
        results = data["results"]
        usernames = {u["username"] for u in results}

        # 排除自己
        self.assertNotIn("A", usernames)

        # 应包含 3 个候选用户（B, C, D）
        self.assertEqual(len(usernames), 3)
        self.assertSetEqual(usernames, {"B", "C", "D"})

    def test_exclude_followed_users(self):
        """测试排除已关注用户"""
        # A 关注了 B（注意：使用 follower 和 following）
        UserFollow.objects.create(follower=self.user, following=self.u1)
        url = "/api/recommend_users/"

        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)
        
        results = resp.json()["results"]
        usernames = {u["username"] for u in results}

        # B 应被排除
        self.assertNotIn("B", usernames)
        # 应该只剩 C 和 D
        self.assertEqual(len(usernames), 2)
        self.assertSetEqual(usernames, {"C", "D"})

    def test_mutual_watch_count_field(self):
        """测试返回共同追番数字段"""
        url = "/api/recommend_users/"

        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)
        
        results = resp.json()["results"]

        # 每个用户必须包含 mutual_watch_count 字段
        for u in results:
            self.assertIn("mutual_watch_count", u)
            self.assertIsInstance(u["mutual_watch_count"], int)
            self.assertGreaterEqual(u["mutual_watch_count"], 0)

    def test_sort_by_mutual_watch(self):
        """测试按共同追番数排序"""
        url = "/api/recommend_users/"

        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)
        
        results = resp.json()["results"]

        # 验证共同追番数的计算
        user_counts = {u["username"]: u["mutual_watch_count"] for u in results}
        
        # C 应该有 2 部共同番剧
        self.assertEqual(user_counts.get("C"), 2)
        # B 应该有 1 部共同番剧
        self.assertEqual(user_counts.get("B"), 1)
        # D 应该有 0 部共同番剧
        self.assertEqual(user_counts.get("D"), 0)

        # 验证排序：共同追番数应该是降序（允许相同数值内随机）
        counts = [u["mutual_watch_count"] for u in results]
        sorted_counts = sorted(counts, reverse=True)
        self.assertEqual(counts, sorted_counts)

    def test_randomization_within_same_count(self):
        """测试相同共同追番数内的随机性"""
        # 创建更多相同共同追番数的用户以测试随机性
        u4 = User.objects.create_user(username="E", password="123")
        u5 = User.objects.create_user(username="F", password="123")
        
        # E 和 F 都追 a1（都与 A 共同1部）
        WatchStatus.objects.create(user=u4, anime=self.a1, status="WATCHING")
        WatchStatus.objects.create(user=u5, anime=self.a1, status="WATCHING")

        url = "/api/recommend_users/"
        
        # 多次调用，收集结果
        orders = []
        for _ in range(10):
            resp = self.client.get(url, **self._auth(self.user))
            results = resp.json()["results"]
            # 只关注共同追番数为1的用户的顺序
            same_count_users = [u["username"] for u in results if u["mutual_watch_count"] == 1]
            orders.append(tuple(same_count_users))

        # 至少应该有不同的排列出现（随机打散）
        unique_orders = set(orders)
        self.assertGreater(len(unique_orders), 1, "推荐结果应该存在随机性")

    def test_required_fields_in_response(self):
        """测试返回字段完整性"""
        url = "/api/recommend_users/"
        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)
        
        results = resp.json()["results"]
        
        required_fields = ["id", "username", "mutual_watch_count"]
        optional_fields = ["avatar", "signature"]
        
        for user in results:
            # 必须字段
            for field in required_fields:
                self.assertIn(field, user)
            
            # 验证字段类型
            self.assertIsInstance(user["id"], int)
            self.assertIsInstance(user["username"], str)

    def test_pagination(self):
        """测试分页功能"""
        # 创建更多用户
        for i in range(10):
            u = User.objects.create_user(username=f"User{i}", password="123")
            WatchStatus.objects.create(user=u, anime=self.a1, status="WATCHING")
        url = "/api/recommend_users/?page=1&limit=5"

        resp = self.client.get(url, **self._auth(self.user))
        self.assertEqual(resp.status_code, 200)
        
        data = resp.json()
        self.assertIn("results", data)
        self.assertIn("count", data)
        self.assertLessEqual(len(data["results"]), 5)

    def test_unauthenticated_access(self):
        """测试未认证访问"""
        url = "/api/recommend_users/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 401)

    def test_empty_recommendations(self):
        """测试没有推荐结果的情况"""
        # 创建一个新用户，关注所有其他用户
        new_user = User.objects.create_user(username="Lonely", password="123")
        
        # 关注所有人
        for user in [self.u1, self.u2, self.u3]:
            UserFollow.objects.create(follower=new_user, following=user)

        url = "/api/recommend_users/"
        resp = self.client.get(url, **self._auth(new_user))
        self.assertEqual(resp.status_code, 200)
        
        results = resp.json()["results"]
        # 除了 A，其他都被关注了，所以结果应该很少
        self.assertLessEqual(len(results), 1)