from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from wangumi_app.models import SyncLog


class WeeklySyncAPITests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.payload = {
            "collections": [
                {
                    "title": "平台 A",
                    "platform": "bilibili",
                    "items": [
                        {
                            "external_id": "api-anime-1",
                            "title": "API Anime",
                        }
                    ],
                }
            ]
        }

    @patch("wangumi_app.services.weekly_sync_service.requests.get")
    def test_trigger_weekly_sync_endpoint(self, mock_get):
        response = MagicMock()
        response.json.return_value = self.payload
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        resp = self.client.post("/api/sync/weekly/")
        self.assertEqual(resp.status_code, 200)

        body = resp.json()
        self.assertEqual(body["code"], 0)
        self.assertIn("log_id", body["data"])

        log = SyncLog.objects.get(id=body["data"]["log_id"])
        self.assertEqual(log.created_count, 1)
        self.assertEqual(log.status, SyncLog.Status.SUCCESS)
