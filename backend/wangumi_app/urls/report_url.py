from django.urls import path
from wangumi_app.views.reports_view import ReportView

urlpatterns = [
    path("comments/<int:comment_id>/reports/", ReportView.as_view(), name="create_report")
]