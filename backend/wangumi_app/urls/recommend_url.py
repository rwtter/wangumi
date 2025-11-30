from django.urls import path

from wangumi_app.views.recommend_anime_view import ContactChangeRequestView

urlpatterns = [
    path("recommend_anime/", ContactChangeRequestView.as_view(), name="recommend-anime-list"),
]
