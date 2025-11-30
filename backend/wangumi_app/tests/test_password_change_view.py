from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class PasswordChangeViewTests(APITestCase):
    def setUp(self):
        self.password = "Secret123!"
        self.user = User.objects.create_user(
            username="account_user",
            email="account@example.com",
            password=self.password,
        )
        self.client = APIClient()
        tokens = self.client.post(
            "/api/login/",
            {"username": self.user.username, "password": self.password},
            format="json",
        ).json()
        self.access = tokens["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

    @patch("wangumi_app.views.account_security_view.invalidate_user_sessions_and_tokens")
    def test_password_change_success(self, mock_invalidate):
        response = self.client.post(
            "/api/account/password_change/",
            {"old_password": self.password, "new_password": "NewSecret123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("密码已更新", response.json()["message"])
        mock_invalidate.assert_called_once_with(self.user)

    def test_password_change_wrong_old_password(self):
        response = self.client.post(
            "/api/account/password_change/",
            {"old_password": "bad-pass", "new_password": "Another123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("无法更新密码", response.json()["error"])

    def test_password_change_same_password(self):
        response = self.client.post(
            "/api/account/password_change/",
            {"old_password": self.password, "new_password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("与旧密码不同", response.json()["error"])

    def test_password_change_strength_validation(self):
        response = self.client.post(
            "/api/account/password_change/",
            {"old_password": self.password, "new_password": "123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.json())
