from django.urls import path
from wangumi_app.views.profile_edit_view import (
    ProfileEditView,
    AvatarUploadView,
)

urlpatterns = [
    # 编辑个人资料 - 使用POST方法，路径与查看不同
    path(
        "user/profile/edit",
        ProfileEditView.as_view(),
        name="update-my-profile",
    ),

    # 上传头像
    path(
        "user/avatar",              # 注意：这里从 user/profile/avatar 改成 user/avatar
        AvatarUploadView.as_view(),
        name="upload-avatar",
    ),
]
