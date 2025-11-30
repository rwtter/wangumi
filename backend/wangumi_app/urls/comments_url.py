from django.urls import path
from wangumi_app.views.comments_view import CommentView

urlpatterns = [
    path("comments/", CommentView.as_view(), name="create_comment")
]