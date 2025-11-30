from django.urls import path

from wangumi_app.views.account_security_view import PasswordChangeView
from wangumi_app.views.contact_update_view import (
    ContactChangeConfirmView,
    ContactChangeRequestView,
)

urlpatterns = [
    path("account/password_change/", PasswordChangeView.as_view(), name="password_change"),
    path("account/contact/change/request/", ContactChangeRequestView.as_view(), name="contact_change_request"),
    path("account/contact/change/confirm/", ContactChangeConfirmView.as_view(), name="contact_change_confirm"),
]
