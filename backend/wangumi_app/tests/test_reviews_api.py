
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.contenttypes.models import ContentType
from wangumi_app.models import Anime, Comment

class ReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="123456")
        self.anime = Anime.objects.create(title="A", title_cn="A", description="")
        self.ct = ContentType.objects.get_for_model(Anime)

    def _auth_headers(self, user):
        token = RefreshToken.for_user(user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {str(token)}"}

    def test_requires_auth(self):
        resp = self.client.post("/api/reviews/anime", data={"animeId": self.anime.id, "score": 8}, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_create_review_updates_rating_and_heat(self):
        headers = self._auth_headers(self.user)
        resp = self.client.post("/api/reviews/anime", data={"animeId": self.anime.id, "score": 8}, content_type="application/json", **headers)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.anime.refresh_from_db()
        self.assertEqual(round(self.anime.rating,1), 8.0)
        self.assertEqual(self.anime.popularity, 1)

    def test_update_review_only_changes_rating(self):
        headers = self._auth_headers(self.user)
        # create
        self.client.post("/api/reviews/anime", data={"animeId": self.anime.id, "score": 8}, content_type="application/json", **headers)
        self.anime.refresh_from_db()
        heat_before = self.anime.popularity
        # fetch review id
        review = Comment.objects.get(content_type=self.ct, object_id=self.anime.id, user=self.user)
        # update
        resp = self.client.patch(f"/api/reviews/{review.id}", data={"score": 10}, content_type="application/json", **headers)
        self.assertEqual(resp.status_code, 200, resp.content)
        self.anime.refresh_from_db()
        self.assertEqual(round(self.anime.rating,1), 10.0)
        self.assertEqual(self.anime.popularity, heat_before)
