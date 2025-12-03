# wangumi_app/urls/register_url.py

from django.urls import path
from wangumi_app.views import register_view

urlpatterns = [
    path("register/", register_view.register),
    path("send_verification_code/", register_view.send_verification_code),
    path("verify_code/", register_view.verify_code),
]
