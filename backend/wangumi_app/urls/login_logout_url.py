from django.urls import path
from wangumi_app.views.login_logout_view import LoginView, LogoutView, LogoutAllView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("logout-all/", LogoutAllView.as_view(), name="logout_all"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
