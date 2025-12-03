from django.urls import path
from wangumi_app.views.personal_homepage_list_view import UserFollowingListView,UserFollowerListView,UserAnimeListView


urlpatterns = [
    path("personal_homepage_following_list/<int:user_id>", UserFollowingListView.as_view(), name="personal_homepage_following_list"),
    path("personal_homepage_follower_list/<int:user_id>", UserFollowerListView.as_view(), name="personal_homepage_follower_list"),
    path("personal_homepage_anime_list/<int:user_id>", UserAnimeListView.as_view(), name="personal_homepage_anime_list"),
    ]