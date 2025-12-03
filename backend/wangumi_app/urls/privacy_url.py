from django.urls import path
from wangumi_app.views import privacy_view as v

urlpatterns = [
    path("users/privacy", v.privacy_settings, name="privacy-settings"),
]
