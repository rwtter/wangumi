from django.urls import path
from wangumi_app.views import profile_view as v
urlpatterns = [
    # 查看他人或自己的公开主页
    path("users/<int:user_id>/profile", v.profile_by_user_id, name="profile-by-id"),
    # 查看“我的主页”（需登录）
    path("user/profile", v.my_profile, name="my-profile"),
]