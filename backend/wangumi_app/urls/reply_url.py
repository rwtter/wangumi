from django.urls import path
from wangumi_app.views.reply_view import ReplyView

urlpatterns = [
    path("comments/<int:comment_id>/replies/", ReplyView.as_view(), name="create_reply")
]