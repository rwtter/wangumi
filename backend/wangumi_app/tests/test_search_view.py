from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector
from wangumi_app.models import Anime, Person, Character, UserProfile
from rest_framework.test import APITestCase
from rest_framework import status


class SearchViewTests(APITestCase):
    """搜索功能测试"""

    def setUp(self):
        """设置测试数据"""
        # 创建用户
        self.user = User.objects.create_user(username="testuser", password="123456")
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            nickname="TestNickname",
            signature="这是一个测试签名",
            avatar="avatars/test_avatar.jpg"
        )

        # 创建另一个用户用于测试
        self.user2 = User.objects.create_user(username="testuser2", password="123456")
        self.user_profile2 = UserProfile.objects.create(
            user=self.user2,
            nickname="Kyosuke Higuchi",  # 对应你说的角色名
            signature="Technology Development Manager",
            avatar="avatars/avatar_DwphTcl.jpg"
        )

        # 创建第三个用户
        self.user3 = User.objects.create_user(username="testuser3", password="123456")
        self.user_profile3 = UserProfile.objects.create(
            user=self.user3,
            nickname="Light Yagami",
            signature="High School Student",
            avatar="avatars/avatar_light.jpg"
        )

        # 创建番剧 (is_admin=True)
        self.anime1 = Anime.objects.create(
            title="Naruto",
            title_cn="火影忍者",
            description="忍者冒险故事",
            is_admin=True,
            popularity=100,
            rating=8.5
        )
        self.anime2 = Anime.objects.create(
            title="One Piece",
            title_cn="海贼王",
            description="海盗冒险故事",
            is_admin=True,
            popularity=90,
            rating=9.0
        )

        # 创建用户自定义条目 (is_admin=False)
        self.item1 = Anime.objects.create(
            title="Custom Anime",
            title_cn="自定义动漫",
            description="用户创建的动漫条目",
            is_admin=False,
            popularity=10,
            rating=7.0
        )

        # 创建制作人员
        self.person1 = Person.objects.create(
            pers_name="Masashi Kishimoto",
            summary="火影忍者作者",
            pers_type=1
        )
        self.person2 = Person.objects.create(
            pers_name="Eiichiro Oda",
            summary="海贼王作者",
            pers_type=1
        )

        # 创建虚拟角色
        self.character1 = Character.objects.create(
            name="Naruto Uzumaki",
            summary="火影忍者主角",
            role_type=1
        )
        self.character2 = Character.objects.create(
            name="Monkey D. Luffy",
            summary="海贼王主角",
            role_type=1
        )

        # 更新搜索向量（模拟实际搜索向量的创建）
        Anime.objects.all().update(search_vector=SearchVector('title', 'title_cn', 'description'))
        Person.objects.all().update(search_vector=SearchVector('pers_name', 'summary'))
        Character.objects.all().update(search_vector=SearchVector('name', 'summary'))
        # UserProfile 只使用直接字段，不使用跨关系引用
        UserProfile.objects.all().update(search_vector=SearchVector('nickname', 'signature'))

    def test_search_trigger_with_keyword(self):
        """测试输入关键词后能正确触发搜索"""
        # 测试搜索"Naruto"
        response = self.client.get('/api/search/?query=Naruto')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], 'Naruto')
        self.assertIn('results', data)
        self.assertIn('total', data)
        self.assertIn('has_result', data)

        # 应该找到包含"火影"的结果
        self.assertTrue(data['has_result'])
        self.assertGreater(data['total'], 0)

    def test_search_empty_keyword(self):
        """测试空关键词搜索"""
        response = self.client.get('/api/search/?query=')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], '')
        self.assertEqual(data['total'], 0)
        self.assertFalse(data['has_result'])

    def test_search_all_types_included(self):
        """测试搜索范围包括番剧、条目、制作团队、虚拟角色"""
        response = self.client.get('/api/search/?query=Naruto')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 验证搜索结果包含所有类型
        self.assertIn('anime', results)
        self.assertIn('item', results)
        self.assertIn('person', results)

        # Naruto应该在anime类型中被找到
        anime_results = results['anime']
        anime_ids = [item['id'] for item in anime_results]
        self.assertIn(self.anime1.id, anime_ids)

    def test_search_anime_type_only(self):
        """测试只搜索番剧类型"""
        response = self.client.get('/api/search/?query=Naruto&type=anime')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 应该只有anime类型的结果
        self.assertEqual(len(results), 1)
        self.assertIn('anime', results)

        # 验证结果中的is_admin字段都是True（番剧）
        anime_results = results['anime']
        for item in anime_results:
            self.assertTrue(item['is_admin'])

    def test_search_item_type_only(self):
        """测试只搜索条目类型"""
        response = self.client.get('/api/search/?query=Custom&type=item')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 应该只有item类型的结果
        self.assertEqual(len(results), 1)
        self.assertIn('item', results)

        # 验证结果中的is_admin字段都是False（条目）
        item_results = results['item']
        for item in item_results:
            self.assertFalse(item['is_admin'])

    def test_search_person_type_only(self):
        """测试只搜索制作人员类型"""
        response = self.client.get('/api/search/?query=Masashi&type=person')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 应该只有person类型的结果
        self.assertEqual(len(results), 1)
        self.assertIn('person', results)

    def test_search_sort_by_relevance(self):
        """测试按相关性排序（默认）"""
        response = self.client.get('/api/search/?query=冒险&sort=relevance')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 验证相关性排序（按related_score降序）
        if results.get('anime'):
            anime_scores = [item['related_score'] for item in results['anime']]
            self.assertEqual(anime_scores, sorted(anime_scores, reverse=True))

    def test_search_sort_by_popularity(self):
        """测试按热度排序"""
        response = self.client.get('/api/search/?query=&sort=popularity')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 对于空查询，应该返回按热度排序的结果
        # 但由于我们的实现会先过滤空查询，这里主要测试sort参数不报错
        self.assertIsInstance(results, dict)

    def test_search_sort_by_time(self):
        """测试按时间排序"""
        response = self.client.get('/api/search/?query=&sort=time')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        results = data['results']

        # 测试sort参数处理
        self.assertIsInstance(results, dict)

    def test_search_pagination_single_type(self):
        """测试单类型搜索的分页功能"""
        # 创建更多测试数据
        for i in range(25):
            Anime.objects.create(
                title=f"Anime {i}",
                title_cn=f"动漫 {i}",
                description=f"第{i}个动漫",
                is_admin=True
            )

        # 重新更新搜索向量
        Anime.objects.all().update(search_vector=SearchVector('title', 'title_cn', 'description'))

        # 测试第一页
        response = self.client.get('/api/search/?query=Anime&type=anime&page=1&limit=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('anime', data['results'])
        self.assertLessEqual(len(data['results']['anime']), 10)

        # 测试第二页
        response = self.client.get('/api/search/?query=Anime&type=anime&page=2&limit=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('anime', data['results'])

    def test_search_has_result_field(self):
        """测试has_result字段是否正确设置"""
        # 测试有结果的情况
        response = self.client.get('/api/search/?query=Naruto')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['has_result'])
        self.assertGreater(data['total'], 0)

        # 测试无结果的情况
        response = self.client.get('/api/search/?query=NonexistentContent')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertFalse(data['has_result'])
        self.assertEqual(data['total'], 0)

    def test_search_response_structure(self):
        """测试搜索响应的数据结构"""
        response = self.client.get('/api/search/?query=test')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        # 验证响应结构
        required_fields = ['query', 'results', 'total', 'has_result']
        for field in required_fields:
            self.assertIn(field, data)

        # 验证结果项的结构
        if data.get('results', {}).get('anime'):
            item = data['results']['anime'][0]
            item_fields = ['id', 'title', 'cover_url', 'related_score', 'is_admin']
            for field in item_fields:
                self.assertIn(field, item)

    # ========= 用户搜索测试 =========

    def test_search_user_with_keyword(self):
        """测试搜索用户功能"""
        # 测试搜索昵称
        response = self.client.get('/api/search/?query=TestNickname&type=user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], 'TestNickname')
        self.assertEqual(data['total'], 1)
        self.assertTrue(data['has_result'])

        # 验证返回的用户信息
        user_results = data['results']['user']
        self.assertEqual(len(user_results), 1)

        user = user_results[0]
        self.assertIn('id', user)
        self.assertIn('name', user)  # 用户名
        self.assertIn('avatar_url', user)  # 头像
        self.assertIn('related_score', user)
        self.assertFalse(user['is_admin'])  # 用户不是管理员

    def test_search_user_by_character_name(self):
        """测试通过角色名搜索用户"""
        # 测试搜索"Higuchi"（你提到的 Kyosuke Higuchi）
        response = self.client.get('/api/search/?query=Higuchi&type=user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], 'Higuchi')
        self.assertGreater(data['total'], 0)
        self.assertTrue(data['has_result'])

        # 验证找到的用户包含正确信息
        user_results = data['results']['user']
        found_higuchi = any('Higuchi' in user.get('name', '') or
                            'Higuchi' in user.get('avatar_url', '')
                            for user in user_results)
        self.assertTrue(found_higuchi)

    def test_search_user_by_anime_character(self):
        """测试搜索动漫角色名对应的用户"""
        # 测试搜索"Light"（Light Yagami）
        response = self.client.get('/api/search/?query=Light&type=user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], 'Light')
        self.assertGreater(data['total'], 0)

        # 验证找到的用户
        user_results = data['results']['user']
        found_light = any('Light' in user.get('name', '') or
                        'Light' in user.get('avatar_url', '')
                        for user in user_results)
        self.assertTrue(found_light)

    def test_search_user_in_all_types(self):
        """测试全类型搜索中包含用户"""
        response = self.client.get('/api/search/?query=Yagami')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('user', data['results'])

        # 验证用户结果中包含 Light Yagami
        user_results = data['results']['user']
        found_yagami = any('Yagami' in user.get('name', '') or
                          'Yagami' in user.get('avatar_url', '')
                          for user in user_results)
        self.assertTrue(found_yagami)

    def test_search_user_no_results(self):
        """测试搜索不存在的用户"""
        response = self.client.get('/api/search/?query=NonexistentUser&type=user')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(data['query'], 'NonexistentUser')
        self.assertEqual(data['total'], 0)
        self.assertFalse(data['has_result'])
        self.assertEqual(len(data['results']['user']), 0)

    def test_search_user_pagination(self):
        """测试用户搜索的分页功能"""
        # 创建更多用户
        for i in range(15):
            User.objects.create_user(username=f"testuser_{i}", password="123456")
            UserProfile.objects.create(
                user=User.objects.get(username=f"testuser_{i}"),
                nickname=f"Test User {i}",
                signature=f"签名 {i}"
            )

        response = self.client.get('/api/search/?query=Test&type=user&page=1&limit=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        user_results = data['results']['user']
        self.assertLessEqual(len(user_results), 5)  # 限制为5个