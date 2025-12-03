from django.urls import path

from wangumi_app.views import password_reset_view

urlpatterns = [
    path("password_reset/request/", password_reset_view.request_password_reset),
    path("password_reset/confirm/", password_reset_view.confirm_password_reset),
]
