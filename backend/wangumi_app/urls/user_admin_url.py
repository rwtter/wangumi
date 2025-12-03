from django.urls import path
from wangumi_app.views.user_admin_views import UserListStatusView, UserStatusView, BanUserView, UnbanUserView

urlpatterns = [
    # ... 其他路由
    
    # 用户封禁管理接口
    path('admin/users/', UserListStatusView.as_view(), name='admin-user-list'),  # 新增：获取所有用户列表
    path('admin/users/<int:user_id>/status/', UserStatusView.as_view(), name='admin-user-status'),  # 原有：获取单个用户状态
    path('admin/users/<int:user_id>/ban/', BanUserView.as_view(), name='admin-user-ban'),  # 原有：封禁用户
    path('admin/users/<int:user_id>/unban/', UnbanUserView.as_view(), name='admin-user-unban'),  # 原有：解封用户
]