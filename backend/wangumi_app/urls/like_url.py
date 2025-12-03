from django.urls import path
from wangumi_app.views.like_view import LikeView

urlpatterns = [
    path("comments/<int:comment_id>/like/", LikeView.as_view(), name="like_comment")
]