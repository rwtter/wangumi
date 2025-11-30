from django.urls import path
from wangumi_app.views.user_activities_view import UserActivityView


urlpatterns = [
    path("user_activities/", UserActivityView.as_view(), name="user_activities")
    ]