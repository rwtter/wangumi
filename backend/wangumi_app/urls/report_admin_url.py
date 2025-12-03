from django.urls import path
from wangumi_app.views.report_admin_views import ReportListView, ReportDetailView, ReportHandleView

urlpatterns = [
    path('admin/reports/', ReportListView.as_view(), name='admin-report-list'),
    path('admin/reports/<int:report_id>/', ReportDetailView.as_view(), name='admin-report-detail'),
    path('admin/reports/<int:report_id>/handle/', ReportHandleView.as_view(), name='admin-report-handle'),
]