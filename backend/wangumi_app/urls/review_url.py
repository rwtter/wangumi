
from django.urls import path
from wangumi_app.views.reviews_view import CreateAnimeReviewView, UpdateReviewView, GetAnimeReviewView

urlpatterns = [
    path("reviews/anime", CreateAnimeReviewView.as_view(), name="review-create"),
    path("reviews/anime/get", GetAnimeReviewView.as_view(), name="review-get"),
    path("reviews/<int:review_id>", UpdateReviewView.as_view(), name="review-update")
]



