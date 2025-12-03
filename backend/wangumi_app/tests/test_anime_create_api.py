from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

from wangumi_app.models import Anime


class AnimeCreateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="creator", password="123456")
        self.other_user = User.objects.create_user(username="other", password="123456")
        self.staff_user = User.objects.create_user(username="staffer", password="123456", is_staff=True)

    def _auth_headers(self, user):
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

    def _create_anime(self, user, title="My Title"):
        headers = self._auth_headers(user)
        resp = self.client.post("/api/anime", data={"title": title}, **headers)
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()["data"]["id"]

    def test_create_requires_auth(self):
        resp = self.client.post("/api/anime", data={"title": "New Anime"})
        self.assertEqual(resp.status_code, 401)

    def test_create_missing_title(self):
        headers = self._auth_headers(self.user)
        resp = self.client.post("/api/anime", data={})
        self.assertEqual(resp.status_code, 401)

        resp = self.client.post("/api/anime", data={}, **headers)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("标题不能为空", resp.content.decode("utf-8"))

    def test_create_success_and_detail(self):
        headers = self._auth_headers(self.user)
        payload = {
            "title": "My Title",
            "title_cn": "标题",
            "description": "简介",
            "genres": "Action,Drama",
            "total_episodes": 12,
        }
        resp = self.client.post("/api/anime", data=payload, **headers)
        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()["data"]
        anime_id = data["id"]
        resp2 = self.client.get(f"/api/anime/{anime_id}")
        self.assertEqual(resp2.status_code, 200)
        detail = resp2.json()["data"]
        self.assertEqual(detail["basic"]["title"], "My Title")
        self.assertEqual(detail["meta"]["createdBy"], "creator")
        self.assertIsNotNone(detail["meta"]["createdAt"])
        self.assertFalse(detail["meta"]["isAdmin"])

    def test_create_with_cover_url(self):
        headers = self._auth_headers(self.user)
        payload = {
            "title": "Remote Cover",
            "cover_url": "https://example.com/cover.jpg",
        }
        resp = self.client.post("/api/anime", data=payload, **headers)
        self.assertEqual(resp.status_code, 201, resp.content)
        anime_id = resp.json()["data"]["id"]
        resp2 = self.client.get(f"/api/anime/{anime_id}")
        self.assertEqual(resp2.status_code, 200)
        detail = resp2.json()["data"]
        self.assertEqual(detail["basic"]["cover"], "https://example.com/cover.jpg")

    def test_staff_creation_sets_is_admin_flag(self):
        anime_id = self._create_anime(self.staff_user, title="Admin Title")
        resp = self.client.get(f"/api/anime/{anime_id}")
        self.assertEqual(resp.status_code, 200)
        detail = resp.json()["data"]
        self.assertTrue(detail["meta"]["isAdmin"])

    def test_delete_requires_authentication(self):
        anime_id = self._create_anime(self.user, title="Need Auth")
        resp = self.client.delete(f"/api/anime/{anime_id}")
        self.assertEqual(resp.status_code, 401)
        self.assertTrue(Anime.objects.filter(id=anime_id).exists())

    def test_creator_can_delete_own_entry(self):
        anime_id = self._create_anime(self.user, title="Self Delete")
        resp = self.client.delete(f"/api/anime/{anime_id}", **self._auth_headers(self.user))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Anime.objects.filter(id=anime_id).exists())

    def test_non_owner_cannot_delete_entry(self):
        anime_id = self._create_anime(self.user, title="Owner Entry")
        resp = self.client.delete(f"/api/anime/{anime_id}", **self._auth_headers(self.other_user))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Anime.objects.filter(id=anime_id).exists())

    def test_non_admin_cannot_delete_admin_entry(self):
        anime_id = self._create_anime(self.staff_user, title="Admin Entry")
        resp = self.client.delete(f"/api/anime/{anime_id}", **self._auth_headers(self.user))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Anime.objects.filter(id=anime_id).exists())

    def test_admin_can_delete_admin_entry(self):
        anime_id = self._create_anime(self.staff_user, title="Admin Own Entry")
        resp = self.client.delete(f"/api/anime/{anime_id}", **self._auth_headers(self.staff_user))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Anime.objects.filter(id=anime_id).exists())
