"""
Tests for the anime list API view.
"""

from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from wangumi_app.models import (
    Anime,
    AnimeStaff,
    Character,
    CharacterAppearance,
    CharacterVoice,
    Episode,
    Person,
    StaffRole,
)


class AnimeListViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.a1 = Anime.objects.create(
            title="Alpha",
            title_cn="Alpha CN",
            rating=7.4,
            popularity=120,
            genres=["Action", "Comedy"],
        )
        self.a2 = Anime.objects.create(
            title="Bravo",
            title_cn="Bravo CN",
            rating=9.1,
            popularity=80,
            genres=["Drama"],
        )
        self.a3 = Anime.objects.create(
            title="Charlie",
            title_cn="Charlie CN",
            rating=8.6,
            popularity=250,
            genres=["Action"],
        )

        now = timezone.now()
        Anime.objects.filter(pk=self.a1.pk).update(updated_at=now - timedelta(days=2))
        Anime.objects.filter(pk=self.a2.pk).update(updated_at=now - timedelta(days=1))
        Anime.objects.filter(pk=self.a3.pk).update(updated_at=now)

        self.a1.refresh_from_db()
        self.a2.refresh_from_db()
        self.a3.refresh_from_db()

    def test_sort_by_rating(self):
        response = self.client.get("/api/anime", {"sort": "评分"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Bravo", "Charlie", "Alpha"])

    def test_sort_by_popularity_default(self):
        response = self.client.get("/api/anime")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Charlie", "Alpha", "Bravo"])

    def test_sort_by_time(self):
        response = self.client.get("/api/anime", {"sort": "时间"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Charlie", "Bravo", "Alpha"])

    def test_pagination(self):
        response = self.client.get("/api/anime", {"limit": 2, "page": 2})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        data = payload["data"]
        self.assertEqual(data["pagination"]["page"], 2)
        self.assertEqual(data["pagination"]["limit"], 2)
        self.assertEqual(data["pagination"]["total"], 3)
        self.assertEqual(len(data["list"]), 1)
        self.assertEqual(data["list"][0]["title"], "Bravo")

    def test_invalid_sort(self):
        response = self.client.get("/api/anime", {"sort": "unknown"})
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["code"], 1)
        self.assertIn("sort 参数仅支持", payload["message"])

    def test_category_filter_single(self):
        response = self.client.get("/api/anime", {"category": "Action"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Charlie", "Alpha"])

    def test_category_filter_multiple(self):
        response = self.client.get("/api/anime", {"category": "Action,Drama"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 0)
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["Charlie", "Alpha", "Bravo"])


class UserEntryListViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.official = Anime.objects.create(
            title="Official",
            title_cn="Official CN",
            popularity=999,
            is_admin=True,
            genres=["Action"],
        )
        self.user_action = Anime.objects.create(
            title="User Action",
            title_cn="User Action CN",
            popularity=100,
            is_admin=False,
            genres=["Action"],
        )
        self.user_drama = Anime.objects.create(
            title="User Drama",
            title_cn="User Drama CN",
            popularity=80,
            is_admin=False,
            genres=["Drama"],
        )

    def test_only_user_entries_returned(self):
        response = self.client.get("/api/anime/user_entries")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertIn("User Action", titles)
        self.assertIn("User Drama", titles)
        self.assertNotIn("Official", titles)

    def test_category_filter_still_applied(self):
        response = self.client.get("/api/anime/user_entries", {"category": "Drama"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        titles = [item["title"] for item in payload["data"]["list"]]
        self.assertEqual(titles, ["User Drama"])


class AnimeDetailViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.anime = Anime.objects.create(
            title="Detail Anime",
            title_cn="ディテールアニメ",
            rating=8.2,
            popularity=500,
            genres=["Action", "Drama"],
            status="FINISHED",
            total_episodes=12,
        )

        Episode.objects.create(anime=self.anime, episode_number=10, title="Ep10")

        self.person = Person.objects.create(
            pers_name="Yuki",
            pers_type=1,
            summary="",
            pers_img="yuki.jpg",
        )

        self.role_director = StaffRole.objects.create(name="导演")
        AnimeStaff.objects.create(anime=self.anime, person=self.person, role=self.role_director)

        self.character = Character.objects.create(name="Hero", image="hero.png")
        CharacterAppearance.objects.create(anime=self.anime, character=self.character, role=1)
        CharacterVoice.objects.create(character=self.character, person=self.person)

    def test_detail_success(self):
        resp = self.client.get(f"/api/anime/{self.anime.id}")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["code"], 0)
        data = payload["data"]
        self.assertEqual(data["basic"]["id"], self.anime.id)
        self.assertEqual(data["meta"]["status"], "已完结")
        self.assertEqual(data["meta"]["updateProgress"], "已更新至第10集")
        self.assertEqual(len(data["relations"]["characters"]), 1)
        self.assertEqual(data["relations"]["characters"][0]["voiceActors"], ["Yuki"])
        self.assertEqual(len(data["relations"]["staff"]), 1)
        self.assertEqual(data["relations"]["staff"][0]["role"], "导演")

    def test_detail_not_found(self):
        resp = self.client.get("/api/anime/999")
        self.assertEqual(resp.status_code, 404)
        payload = resp.json()
        self.assertEqual(payload["code"], 404)
        self.assertIsNone(payload["data"])
