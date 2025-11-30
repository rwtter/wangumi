import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase


class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = "user@example.com"
        self.user = User.objects.create_user(
            username="tester",
            email=self.email,
            password="secret123",
        )
        cache.clear()

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=987654)
    def test_password_reset_flow(self, _mock_randint):
        request_payload = json.dumps({"email": self.email})
        resp = self.client.post(
            "/api/password_reset/request/",
            data=request_payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)

        resp = self.client.post(
            "/api/password_reset/confirm/",
            data=json.dumps(
                {"email": self.email, "code": "987654", "new_password": "newpass123"}
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=111222)
    def test_password_reset_invalid_code(self, _mock_randint):
        self.client.post(
            "/api/password_reset/request/",
            data=json.dumps({"email": self.email}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/password_reset/confirm/",
            data=json.dumps(
                {"email": self.email, "code": "000000", "new_password": "another123"}
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("验证码无效", resp.json()["error"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("secret123"))
