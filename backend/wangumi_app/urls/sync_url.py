from django.urls import path

from wangumi_app.views.sync_view import SeasonSyncView, WeeklySyncView

urlpatterns = [
    path("sync/weekly/", WeeklySyncView.as_view(), name="sync-weekly"),
    path("sync/season/", SeasonSyncView.as_view(), name="sync-season"),
]
