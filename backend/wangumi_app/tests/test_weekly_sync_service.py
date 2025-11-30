from datetime import date
from unittest.mock import MagicMock, patch

from django.test import TestCase

from wangumi_app.models import Anime, SyncLog
from wangumi_app.services.weekly_sync_service import sync_weekly_collections


class WeeklySyncServiceTests(TestCase):
    def setUp(self):
        self.payload = {
            "collections": [
                {
                    "title": "平台 A",
                    "platform": "bilibili",
                    "cover": "https://example.com/collection-cover.jpg",
                    "items": [
                        {
                            "external_id": "anime-1",
                            "title": "Anime 1",
                            "title_cn": "番剧 1",
                            "cover": "https://example.com/cover1.jpg",
                            "platform": "bilibili",
                            "genres": ["Action"],
                            "airtime": "Sunday",
                            "total_episodes": 12,
                            "release_date": "2025-01-01",
                        },
                        {
                            "external_id": "anime-2",
                            "name": "Anime 2",
                            "cover": "https://example.com/cover2.jpg",
                            "platform": "bilibili",
                        },
                    ],
                }
            ]
        }
        Anime.objects.create(
            external_id="anime-1",
            title="Old title",
            title_cn="旧标题",
            cover_url="",
            platform="bilibili",
        )

    @patch("wangumi_app.services.weekly_sync_service.requests.get")
    def test_sync_creates_and_updates_anime(self, mock_get):
        response = MagicMock()
        response.json.return_value = self.payload
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        success, stats = sync_weekly_collections()

        self.assertTrue(success)
        self.assertEqual(stats["created"], 1)
        self.assertEqual(stats["updated"], 1)

        anime = Anime.objects.get(external_id="anime-1")
        self.assertEqual(anime.title, "Anime 1")
        self.assertEqual(anime.title_cn, "番剧 1")
        self.assertEqual(anime.cover_url, "https://example.com/cover1.jpg")
        self.assertTrue(anime.is_weekly_featured)
        self.assertEqual(anime.release_date, date(2025, 1, 1))

        created_anime = Anime.objects.get(external_id="anime-2")
        self.assertEqual(created_anime.title, "Anime 2")
        self.assertEqual(created_anime.cover_url, "https://example.com/cover2.jpg")

        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.job_type, SyncLog.JobType.WEEKLY)
        self.assertEqual(log.status, SyncLog.Status.SUCCESS)
        self.assertEqual(log.created_count, 1)
        self.assertEqual(log.updated_count, 1)
        self.assertIn("created=1", log.message)
