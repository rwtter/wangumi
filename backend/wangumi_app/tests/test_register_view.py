import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, TestCase

from wangumi_app.models import UserProfile


class SmsVerificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.email = "user@example.com"
        self.phone = "13800000000"
        cache.clear()

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=123456)
    def test_send_verification_code(self, _mock_randint):
        resp = self.client.post(
            "/api/send_verification_code/",
            data=json.dumps({"email": self.email, "purpose": "register"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["message"], "验证码已发送")
        self.assertEqual(payload["data"]["purpose"], "register")

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=123456)
    def test_verify_code_endpoint(self, _mock_randint):
        self.client.post(
            "/api/send_verification_code/",
            data=json.dumps({"email": self.email, "purpose": "register"}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/verify_code/",
            data=json.dumps(
                {"email": self.email, "purpose": "register", "code": "123456", "consume": False}
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["message"], "验证码已验证")

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=123456)
    def test_register_success_with_sms_code(self, _mock_randint):
        self.client.post(
            "/api/send_verification_code/",
            data=json.dumps({"email": self.email, "purpose": "register"}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/register/",
            data=json.dumps(
                {
                    "username": "test_user",
                    "password": "secret123",
                    "email": self.email,
                    "code": "123456",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertEqual(payload["message"], "注册成功")
        self.assertTrue(User.objects.filter(username="test_user").exists())

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=123456)
    def test_register_fail_with_wrong_code(self, _mock_randint):
        self.client.post(
            "/api/send_verification_code/",
            data=json.dumps({"email": "fail@example.com", "purpose": "register"}),
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/register/",
            data=json.dumps(
                {
                    "username": "test_user2",
                    "password": "secret123",
                    "email": "fail@example.com",
                    "code": "000000",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("验证码无效", resp.json()["error"])
        self.assertFalse(User.objects.filter(username="test_user2").exists())

    @patch("wangumi_app.services.sms_verification.random.randint", return_value=123456)
    def test_send_verification_code_rate_limited(self, _mock_randint):
        payload = json.dumps({"email": self.email, "purpose": "register"})
        self.client.post(
            "/api/send_verification_code/",
            data=payload,
            content_type="application/json",
        )
        resp = self.client.post(
            "/api/send_verification_code/",
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 429)
        self.assertIn("请求过于频繁", resp.json()["error"])
