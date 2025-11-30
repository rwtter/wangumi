from django.urls import path
from wangumi_app.views.recommend_social_view import UserRecommendationView, recommendItemItemRecommendationView

urlpatterns = [
    path("recommend_users/", UserRecommendationView.as_view(), name="recommend_users"),
    path("recommend_items/", recommendItemItemRecommendationView.as_view(), name="recommend_items"),
]
