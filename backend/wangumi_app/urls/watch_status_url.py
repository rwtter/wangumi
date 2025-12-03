from django.urls import path
from wangumi_app.views.watch_status_view import WatchStatusView

urlpatterns = [
    path("watch-status/", WatchStatusView.as_view(), name="watch_status")]