from datetime import date
from unittest.mock import MagicMock, patch

from django.test import TestCase

from wangumi_app.models import Anime, SyncLog
from wangumi_app.services.season_sync_service import sync_current_season_anime


class SeasonSyncServiceTests(TestCase):
    def setUp(self):
        self.payload = [
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
        ]

        Anime.objects.create(
            external_id="anime-1",
            title="Old title",
            title_cn="旧标题",
            cover_url="",
            platform="bilibili",
        )

    @patch("wangumi_app.services.season_sync_service.get_current_season_year_and_quarter", return_value=(2025, "winter"))
    @patch("wangumi_app.services.season_sync_service.requests.get")
    def test_sync_creates_and_updates_anime(self, mock_get, mock_quarter):
        response = MagicMock()
        response.json.return_value = self.payload
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        success, stats = sync_current_season_anime()

        self.assertTrue(success)
        self.assertEqual(stats["created"], 1)
        self.assertEqual(stats["updated"], 1)

        anime = Anime.objects.get(external_id="anime-1")
        self.assertEqual(anime.title, "Anime 1")
        self.assertEqual(anime.title_cn, "番剧 1")
        self.assertEqual(anime.cover_url, "https://example.com/cover1.jpg")
        self.assertTrue(anime.is_season_featured)
        self.assertEqual(anime.season_year, 2025)
        self.assertEqual(anime.season_quarter, "winter")
        self.assertEqual(anime.release_date, date(2025, 1, 1))

        created_anime = Anime.objects.get(external_id="anime-2")
        self.assertEqual(created_anime.title, "Anime 2")
        self.assertEqual(created_anime.cover_url, "https://example.com/cover2.jpg")
        self.assertEqual(created_anime.season_year, 2025)
        self.assertEqual(created_anime.season_quarter, "winter")

        log = SyncLog.objects.latest("started_at")
        self.assertEqual(log.job_type, SyncLog.JobType.SEASON)
        self.assertEqual(log.status, SyncLog.Status.SUCCESS)
        self.assertEqual(log.created_count, 1)
        self.assertEqual(log.updated_count, 1)
        self.assertIn("created=1", log.message)
