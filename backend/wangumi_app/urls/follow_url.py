# -*- coding: utf-8 -*-
# wangumi_app/urls/follow_url.py
from django.urls import path
from wangumi_app.views import follow_view

urlpatterns = [
    
    path("users/<int:id>/follow", follow_view.follow_user, name="follow_user"),
    path("users/<int:id>/unfollow", follow_view.unfollow_user, name="unfollow_user"),
]
