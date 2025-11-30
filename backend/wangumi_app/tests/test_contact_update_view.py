from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from wangumi_app.models import UserProfile


class ContactUpdateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "Secret123!"
        self.user = User.objects.create_user(
            username="contact_user",
            email="old@example.com",
            password=self.password,
        )
        self.profile = UserProfile.objects.create(user=self.user, cellphone="13800000000")
        tokens = self.client.post(
            "/api/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        ).json()
        self.access = tokens["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    @patch("wangumi_app.views.contact_update_view.send_email_code")
    def test_request_email_change_success(self, mock_send):
        resp = self.client.post(
            "/api/account/contact/change/request/",
            {
                "contact_type": "email",
                "value": "new@example.com",
                "current_password": self.password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        mock_send.assert_called_once()

    def test_request_email_conflict(self):
        User.objects.create_user(
            username="other",
            email="occupied@example.com",
            password="another123",
        )
        resp = self.client.post(
            "/api/account/contact/change/request/",
            {
                "contact_type": "email",
                "value": "occupied@example.com",
                "current_password": self.password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 409)

    @patch("wangumi_app.views.contact_update_view.verify_email_code", return_value=True)
    def test_confirm_email_change_success(self, mock_verify):
        resp = self.client.post(
            "/api/account/contact/change/confirm/",
            {
                "contact_type": "email",
                "value": "brand@example.com",
                "code": "123456",
                "current_password": self.password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "brand@example.com")
        mock_verify.assert_called_once()

    @patch("wangumi_app.views.contact_update_view.verify_email_code", return_value=False)
    def test_confirm_email_change_bad_code(self, _mock_verify):
        resp = self.client.post(
            "/api/account/contact/change/confirm/",
            {
                "contact_type": "email",
                "value": "brand@example.com",
                "code": "000000",
                "current_password": self.password,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("验证码无效", resp.json()["error"])
