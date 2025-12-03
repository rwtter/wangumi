"""
测试条目推荐功能的测试文件
测试推荐模式：基于用户的追番、评论、点赞与回复行为，结合条目热度计算兴趣相似度，推荐相关讨论内容
热度权重较高，但不需要返回推荐依据
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import (
    Anime, UserProfile, UserFollow, WatchStatus,
    Comment, Like, Reply
)

User = get_user_model()


class ItemRecommendationAPITest(TestCase):
    """条目推荐API测试类"""

    def _auth_headers(self, user):
        """生成JWT认证头部"""
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

    def setUp(self):
        """测试初始化数据"""
        cache.clear()

        # 创建测试用户
        self.user = User.objects.create_user(username="testuser", password="pass123")
        self.friend = User.objects.create_user(username="frienduser", password="pass123")
        self.other_friend = User.objects.create_user(username="otherfriend", password="pass123")

        # 创建用户资料
        UserProfile.objects.create(user=self.user)
        UserProfile.objects.create(user=self.friend)
        UserProfile.objects.create(user=self.other_friend)

        # 创建内容类型
        self.anime_content_type = ContentType.objects.get_for_model(Anime)

        # 创建条目（is_admin=False - 条目）
        self.item1 = Anime.objects.create(
            title='测试条目1',
            title_cn='测试条目1中文',
            description='这是一个测试条目，动作冒险类型',
            is_admin=False,
            popularity=1000,
            rating=8.5,
            genres=['动作', '冒险']
        )

        self.item2 = Anime.objects.create(
            title='测试条目2',
            title_cn='测试条目2中文',
            description='这是另一个测试条目，科幻类型',
            is_admin=False,
            popularity=800,
            rating=7.8,
            genres=['科幻']
        )

        self.item3 = Anime.objects.create(
            title='测试条目3',
            title_cn='测试条目3中文',
            description='第三个测试条目，热门动作',
            is_admin=False,
            popularity=2000,
            rating=9.0,
            genres=['动作']
        )

        self.item4 = Anime.objects.create(
            title='测试条目4',
            title_cn='测试条目4中文',
            description='第四个测试条目，奇幻冒险',
            is_admin=False,
            popularity=600,
            rating=7.2,
            genres=['奇幻', '冒险']
        )

        # 创建番剧（is_admin=True - 番剧）用于测试过滤
        self.anime = Anime.objects.create(
            title='测试番剧',
            title_cn='测试番剧中文',
            description='这是一个测试番剧，不应该出现在条目推荐中',
            is_admin=True,
            popularity=3000,
            rating=8.0,
            genres=['动作', '冒险']
        )

        # 建立关注关系
        UserFollow.objects.create(follower=self.user, following=self.friend)
        UserFollow.objects.create(follower=self.user, following=self.other_friend)

        # 用户行为数据 - 兴趣推荐
        Comment.objects.create(
            user=self.user,
            content_type=self.anime_content_type,
            object_id=self.item1.id,
            score=9,
            content='用户对条目1的评论',
            scope='ITEM'
        )

        # 好友行为数据
        Comment.objects.create(
            user=self.friend,
            content_type=self.anime_content_type,
            object_id=self.item2.id,
            score=8,
            content='好友对条目2的评论',
            scope='ITEM'
        )

        # 用户点赞行为
        friend_comment = Comment.objects.create(
            user=self.other_friend,
            content_type=self.anime_content_type,
            object_id=self.item3.id,
            score=7,
            content='其他好友对条目3的评论',
            scope='ITEM'
        )
        Like.objects.create(user=self.user, comment=friend_comment, is_active=True)

        # 用户回复行为
        reply_comment = Comment.objects.create(
            user=self.friend,
            content_type=self.anime_content_type,
            object_id=self.item4.id,
            score=8,
            content='被回复的评论',
            scope='ITEM'
        )
        Reply.objects.create(review=reply_comment, user=self.user, content='用户的回复')

        # 用户对番剧也有行为（应该不影响条目推荐）
        Comment.objects.create(
            user=self.user,
            content_type=self.anime_content_type,
            object_id=self.anime.id,
            score=8,
            content='用户对番剧的评论',
            scope='ANIME'
        )

        self.url = "/api/recommend_items/"

    def test_unauthenticated_user_recommendations(self):
        """测试未登录用户的推荐（只返回热门条目）"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["code"], 0)
        self.assertIn("data", data)
        self.assertIn("results", data["data"])

        results = data["data"]["results"]

        # 确保只返回条目（is_admin=False）
        for result in results:
            anime_obj = Anime.objects.get(id=result["id"])
            self.assertFalse(anime_obj.is_admin, "未登录用户应该只看到条目，不是番剧")

    def test_authenticated_user_recommendations(self):
        """测试已登录用户的推荐"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["code"], 0)
        self.assertIn("results", data["data"])

    def test_item_vs_anime_filtering(self):
        """测试条目与番剧的正确过滤"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 验证所有推荐都是条目，不包含番剧
        result_ids = [result["id"] for result in results]
        animes = Anime.objects.filter(id__in=result_ids)

        for anime in animes:
            self.assertFalse(anime.is_admin,
                           f"推荐ID {anime.id} '{anime.title}' 应该是条目，但实际是番剧")

    def test_interest_based_recommendations(self):
        """测试基于兴趣的推荐"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 应该包含用户评论过的相关条目
        result_titles = [result["title"] for result in results]

        # 由于用户评论了item1（动作、冒险），应该推荐相似类型的条目
        action_adventure_items = [item for item in results
                                 if any(genre in ['动作', '冒险']
                                       for genre in Anime.objects.get(id=item["id"]).genres)]

        # 至少应该有一些基于兴趣的推荐
        self.assertGreater(len(action_adventure_items), 0,
                          "应该有基于用户兴趣的推荐（动作、冒险类型）")

    def test_friend_based_recommendations(self):
        """测试基于好友行为的推荐"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 好友评论了item2（科幻），点赞了item3，回复了item4
        # 应该在推荐结果中体现好友行为
        result_ids = [result["id"] for result in results]

        # 检查是否包含好友互动过的条目
        friend_interacted_items = [self.item2.id, self.item3.id, self.item4.id]
        has_friend_recommendations = any(item_id in result_ids for item_id in friend_interacted_items)

        self.assertTrue(has_friend_recommendations,
                       "推荐结果应该包含好友行为影响的条目")

    def test_hot_based_recommendations(self):
        """测试基于热度的推荐"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 验证结果包含高热度条目
        # item3 热度最高(2000)，应该在推荐中
        result_ids = [result["id"] for result in results]
        self.assertIn(self.item3.id, result_ids,
                     "高热度条目应该在推荐结果中")

    def test_recommendation_response_structure(self):
        """测试推荐响应结构"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()

        # 验证标准响应格式
        self.assertIn("code", data)
        self.assertIn("message", data)
        self.assertIn("data", data)

        response_data = data["data"]
        self.assertIn("count", response_data)
        self.assertIn("page", response_data)
        self.assertIn("limit", response_data)
        self.assertIn("results", response_data)

        # 验证推荐结果格式
        if response_data["results"]:
            result = response_data["results"][0]
            required_fields = ["id", "title", "popularity", "score"]
            for field in required_fields:
                self.assertIn(field, result, f"推荐结果应该包含 {field} 字段")

    def test_recommendation_score_calculation(self):
        """测试推荐分数计算"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 验证每个推荐项都有分数且为正数
        for result in results:
            self.assertIn("score", result)
            self.assertIsInstance(result["score"], (int, float))
            self.assertGreater(result["score"], 0, "推荐分数应该大于0")

        # 验证结果按分数降序排列
        if len(results) > 1:
            scores = [result["score"] for result in results]
            self.assertEqual(scores, sorted(scores, reverse=True),
                           "推荐结果应该按分数降序排列")

    def test_pagination_functionality(self):
        """测试分页功能"""
        headers = self._auth_headers(self.user)

        # 创建更多条目数据用于分页测试
        for i in range(10):
            Anime.objects.create(
                title=f'分页测试条目{i}',
                title_cn=f'分页测试条目{i}中文',
                description=f'第{i}个分页测试条目',
                is_admin=False,
                popularity=100 + i * 10,
                rating=7.0 + i * 0.1,
                genres=['测试']
            )

        # 测试第一页
        response = self.client.get(self.url, {"page": 1, "limit": 5}, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        response_data = data["data"]
        self.assertEqual(response_data["page"], 1)
        self.assertEqual(response_data["limit"], 5)
        self.assertLessEqual(len(response_data["results"]), 5)

        # 测试第二页
        if response_data["count"] > 5:
            response2 = self.client.get(self.url, {"page": 2, "limit": 5}, **headers)
            self.assertEqual(response2.status_code, 200)

            data2 = response2.json()
            self.assertEqual(data2["data"]["page"], 2)

    def test_parameter_validation(self):
        """测试参数验证"""
        headers = self._auth_headers(self.user)

        # 测试无效的page参数
        response = self.client.get(self.url, {"page": -1}, **headers)
        self.assertEqual(response.status_code, 400)

        # 测试无效的limit参数
        response = self.client.get(self.url, {"limit": "invalid"}, **headers)
        self.assertEqual(response.status_code, 400)

        # 测试过大的limit参数（应该被限制为100）
        response = self.client.get(self.url, {"limit": 200}, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertLessEqual(len(data["data"]["results"]), 100)

    def test_user_with_no_behavior_data(self):
        """测试没有行为数据的用户"""
        new_user = User.objects.create_user(username="newuser", password="pass123")
        UserProfile.objects.create(user=new_user)

        headers = self._auth_headers(new_user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 应该返回热门推荐
        self.assertGreater(len(results), 0, "没有行为数据的用户应该返回热门推荐")

        # 确保只返回条目
        for result in results:
            anime_obj = Anime.objects.get(id=result["id"])
            self.assertFalse(anime_obj.is_admin, "热门推荐也应该只包含条目")

    def test_no_duplicate_recommendations(self):
        """测试推荐结果去重"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 检查没有重复的条目ID
        result_ids = [result["id"] for result in results]
        self.assertEqual(len(result_ids), len(set(result_ids)),
                        "推荐结果不应该有重复")

    def test_scope_item_filtering(self):
        """测试scope='ITEM'过滤的正确性"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 验证所有推荐都基于scope='ITEM'的评论
        for result in results:
            anime_obj = Anime.objects.get(id=result["id"])

            # 检查是否有scope='ITEM'的评论关联
            item_comments = Comment.objects.filter(
                object_id=anime_obj.id,
                scope='ITEM'
            )

            # 对于非热门推荐，应该有ITEM相关的评论
            # 但由于也可能有热门推荐，所以这个检查不是绝对的
            self.assertTrue(
                anime_obj.popularity > 1500 or item_comments.exists(),
                f"条目 {anime_obj.title} 要么是高热度，要么应该有ITEM相关的评论"
            )

    def test_is_admin_false_filtering(self):
        """测试is_admin=False过滤的正确性"""
        headers = self._auth_headers(self.user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 严格验证：所有推荐的Anime对象的is_admin都必须是False
        result_ids = [result["id"] for result in results]
        animes = Anime.objects.filter(id__in=result_ids)

        for anime in animes:
            self.assertFalse(anime.is_admin,
                           f"推荐ID {anime.id} '{anime.title}' 的is_admin应该为False")

        # 进一步确认：番剧不应该出现在推荐中
        self.assertNotIn(self.anime.id, result_ids,
                        "番剧不应该出现在条目推荐结果中")


class ItemRecommendationIntegrationTest(TestCase):
    """条目推荐集成测试"""

    def _auth_headers(self, user):
        """生成JWT认证头部"""
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

    def setUp(self):
        """集成测试环境设置"""
        cache.clear()

        # 创建多个用户模拟真实环境
        self.main_user = User.objects.create_user(username="mainuser", password="pass123")
        UserProfile.objects.create(user=self.main_user)

        self.friends = []
        for i in range(3):
            friend = User.objects.create_user(username=f"friend{i}", password="pass123")
            UserProfile.objects.create(user=friend)
            self.friends.append(friend)

            # 建立关注关系
            UserFollow.objects.create(follower=self.main_user, following=friend)

        # 创建多种类型的条目
        self.content_type = ContentType.objects.get_for_model(Anime)
        self.items = []

        genres_list = [
            ['动作', '冒险'],
            ['科幻', '未来'],
            ['恋爱', '日常'],
            ['悬疑', '推理'],
            ['喜剧', '校园']
        ]

        for i, genres in enumerate(genres_list):
            item = Anime.objects.create(
                title=f'集成测试条目{i+1}',
                title_cn=f'集成测试条目{i+1}中文',
                description=f'第{i+1}个集成测试条目',
                is_admin=False,
                popularity=500 + i * 200,
                rating=7.0 + i * 0.2,
                genres=genres
            )
            self.items.append(item)

        # 创建用于对比的番剧
        self.anime = Anime.objects.create(
            title='集成测试番剧',
            title_cn='集成测试番剧中文',
            description='用于对比的番剧',
            is_admin=True,
            popularity=2000,
            rating=8.5,
            genres=['动作', '冒险']
        )

        # 设置复杂的用户行为数据
        self._setup_user_behaviors()

        self.url = "/api/recommend_items/"


    def _setup_user_behaviors(self):
        """设置复杂的用户行为数据"""
        # 主用户行为
        Comment.objects.create(
            user=self.main_user,
            content_type=self.content_type,
            object_id=self.items[0].id,  # 动作、冒险
            score=9,
            content='主用户评论',
            scope='ITEM'
        )

        # 好友行为
        for i, friend in enumerate(self.friends):
            # 每个好友对不同条目有行为
            Comment.objects.create(
                user=friend,
                content_type=self.content_type,
                object_id=self.items[i].id,
                score=7 + i,
                content=f'好友{i}评论',
                scope='ITEM'
            )

            # 一些点赞行为
            if i < 2:
                like_comment = Comment.objects.create(
                    user=self.friends[(i+1) % 3],
                    content_type=self.content_type,
                    object_id=self.items[(i+2) % 5].id,
                    score=8,
                    content=f'被点赞的评论{i}',
                    scope='ITEM'
                )
                Like.objects.create(user=friend, comment=like_comment, is_active=True)

    def test_comprehensive_workflow(self):
        """测试完整的推荐工作流程"""
        headers = self._auth_headers(self.main_user)
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        results = data["data"]["results"]

        # 验证所有推荐都是条目
        for result in results:
            anime_obj = Anime.objects.get(id=result["id"])
            self.assertFalse(anime_obj.is_admin,
                           f"集成测试中所有推荐都应该是条目，但ID {result['id']} 是番剧")

        # 验证推荐结果包含相关的条目
        result_ids = [result["id"] for result in results]
        user_interacted_ids = [item.id for item in self.items]

        # 至少应该有一些基于用户行为或相似类型的推荐
        has_interacted_items = any(item_id in result_ids for item_id in user_interacted_ids)
        self.assertTrue(has_interacted_items,
                       "推荐应该包含用户互动过或相似的条目")

    def test_performance_with_large_data(self):
        """测试大量数据下的性能"""
        # 创建更多测试数据
        for i in range(20):
            item = Anime.objects.create(
                title=f'性能测试条目{i}',
                title_cn=f'性能测试条目{i}中文',
                description=f'第{i}个性能测试条目',
                is_admin=False,
                popularity=300 + i * 50,
                rating=6.5 + i * 0.1,
                genres=['性能测试']
            )

            # 为每个条目添加一些评论
            Comment.objects.create(
                user=self.friends[0],
                content_type=self.content_type,
                object_id=item.id,
                score=7,
                content=f'性能测试评论{i}',
                scope='ITEM'
            )

        import time
        headers = self._auth_headers(self.main_user)

        start_time = time.time()
        response = self.client.get(self.url, **headers)
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 5.0, "推荐响应时间应该在5秒以内")

        # 验证在大量数据下仍然只返回条目
        data = response.json()
        results = data["data"]["results"]

        for result in results:
            anime_obj = Anime.objects.get(id=result["id"])
            self.assertFalse(anime_obj.is_admin,
                           "即使在大数据量下，也应该只返回条目")
            #测试gitlab runner