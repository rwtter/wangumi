from django.urls import path

from wangumi_app.views import anime_views

urlpatterns = [
    path("anime", anime_views.AnimeListCreateView.as_view(), name="anime-list"),
    path("anime/user_entries", anime_views.UserEntryListView.as_view(), name="anime-user-list"),
    path("anime/<int:anime_id>", anime_views.anime_detail, name="anime-detail"),
]
