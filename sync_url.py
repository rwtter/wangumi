from django.urls import path

from wangumi_app.views.sync_view import WeeklySyncView

urlpatterns = [
    path("sync/weekly/", WeeklySyncView.as_view(), name="sync-weekly"),
]