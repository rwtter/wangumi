from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import UserProfile, UserFollow, WatchStatus, Anime, PrivacySetting
from wangumi_app.utils import build_error_response
"""
用户主页列表视图
提供关注列表、粉丝列表、番剧列表的API接口
"""


def is_following(viewer, owner):
    """检查viewer是否关注了owner"""
    return UserFollow.objects.filter(follower=viewer, following=owner).exists()

def is_mutual_follow(viewer, owner):
    """检查viewer和owner是否互相关注"""
    return (
        UserFollow.objects.filter(follower=viewer, following=owner).exists() and
        UserFollow.objects.filter(follower=owner, following=viewer).exists()
    )

def get_privacy_setting(user, field_name):
    """获取用户的隐私设置"""
    try:
        privacy_setting = PrivacySetting.objects.get(user=user)
        return getattr(privacy_setting, field_name, "public")
    except PrivacySetting.DoesNotExist:
        # 如果没有隐私设置，默认为公开
        return "public"

def check_privacy(viewer, owner, field_name):
    """检查隐私设置是否允许查看"""
    privacy_setting = get_privacy_setting(owner, field_name)

    if privacy_setting == 'public':
        return True
    elif privacy_setting == 'self':
        return viewer and viewer.id == owner.id
    elif privacy_setting == 'friends':
        return viewer and (viewer.id == owner.id or is_following(viewer, owner))
    elif privacy_setting == 'mutual':
        return viewer and (viewer.id == owner.id or is_mutual_follow(viewer, owner))
    return False

def get_pagination_params(request):
    """获取分页参数，返回 (page, limit)"""
    try:
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
    except ValueError:
        return None, None, build_error_response("page 和 limit 必须是正整数")
    
    if page <= 0 or limit <= 0:
        return None, None, build_error_response("page 和 limit 必须是正整数")
    
    limit = min(limit, 100)  # 限制最大每页数量
    return page, limit, None

class UserFollowingListView(APIView):
    """
    获取用户的关注列表
    GET /api/users/{user_id}/following/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, user_id):
        # 1. 验证查看的用户存在
        user = get_object_or_404(User, pk=user_id)

        # 2. 检查隐私设置
        current_user = request.user if request.user.is_authenticated else None

        if not check_privacy(current_user, user, "followings"):
            return build_error_response("该用户的关注列表不公开", 403)
        
        # 3. 获取分页参数
        page, limit, error_response = get_pagination_params(request)
        if error_response:  
            return error_response
            
        # 4. 查询关注列表
        followings = UserFollow.objects.filter(
            follower=user
        ).select_related('following', 'following__userprofile').order_by('-created_at')
        
        # 5. 分页
        paginator = Paginator(followings, limit)
        page_obj = paginator.get_page(page)
        
        # 6. 构造返回数据
        followings_data = []
        for follow in page_obj:
            following_user = follow.following
            try:
                following_profile = following_user.userprofile
                avatar_url = following_profile.avatar.url if following_profile.avatar else None
            except UserProfile.DoesNotExist:
                avatar_url = None
            
            user_url = f"/api/users/{following_user.id}/"
            followings_data.append({
                'id': following_user.id,
                'username': following_user.username,
                'avatar': avatar_url,
                'followed_at': follow.created_at.isoformat(),
                'user_url': user_url,
            })
        
        return Response({
            'count': paginator.count,
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'results': followings_data
        })


class UserFollowerListView(APIView):
    """
    获取用户的粉丝列表
    GET /api/users/{user_id}/followers/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id):
        # 1. 验证用户存在
        user = get_object_or_404(User, pk=user_id)

        # 2. 检查隐私设置
        current_user = request.user if request.user.is_authenticated else None

        if check_privacy(current_user, user, "followers") is False:
            return build_error_response("该用户的粉丝列表不公开", 403)
        
        # 3. 获取分页参数
        page, limit, error_response = get_pagination_params(request)
        if error_response:  
            return error_response
        
        # 4. 查询粉丝列表
        followers = UserFollow.objects.filter(
            following=user
        ).select_related('follower', 'follower__userprofile').order_by('-created_at')
        
        # 5. 分页
        paginator = Paginator(followers, limit)
        page_obj = paginator.get_page(page)
        
        # 6. 构造返回数据
        followers_data = []
        for follow in page_obj:
            follower_user = follow.follower
            try:
                follower_profile = follower_user.userprofile
                avatar_url = follower_profile.avatar.url if follower_profile.avatar else None
            except UserProfile.DoesNotExist:
                avatar_url = None
            
            followers_data.append({
                'id': follower_user.id,
                'username': follower_user.username,
                'avatar': avatar_url,
                'followed_at': follow.created_at.isoformat(),
            })
        
        return Response({
            'count': paginator.count,
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'results': followers_data
        })


class UserAnimeListView(APIView):
    """
    获取用户的番剧列表
    GET /api/users/{user_id}/anime/
    支持按状态筛选: ?status=WATCHING
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    def get(self, request, user_id):
        # 1. 验证用户存在
        user = get_object_or_404(User, pk=user_id)

        # 2. 检查隐私设置
        current_user = request.user if request.user.is_authenticated else None

        if check_privacy(current_user, user, "watchlist") is False:
            return build_error_response("该用户的番剧列表不公开", 403) 
        
        # 3. 获取分页参数
        page, limit, error_response = get_pagination_params(request)
        if error_response:  
            return error_response
        
        # 4. 获取状态筛选参数
        status_filter = request.GET.get('status', None)
        valid_statuses = ['WANT', 'WATCHING', 'FINISHED']
        
        if status_filter and status_filter not in valid_statuses:
            return build_error_response(f"无效的状态参数，可选值: {', '.join(valid_statuses)}")
        
        # 5. 查询追番列表
        watch_statuses = WatchStatus.objects.filter(
            user=user
        ).select_related('anime').order_by('-updated_at')
        
        # 按状态筛选
        if status_filter:
            watch_statuses = watch_statuses.filter(status=status_filter)
        
        # 6. 分页
        paginator = Paginator(watch_statuses, limit)
        page_obj = paginator.get_page(page)
        
        # 7. 构造返回数据
        anime_data = []
        for watch_status in page_obj:
            anime = watch_status.anime
            
            anime_data.append({
                'id': anime.id,
                'title': anime.title,
                'title_cn': anime.title_cn,
                'cover': anime.cover_url if anime.cover_url else (
                    anime.cover_image.url if anime.cover_image else None
                ),
                'rating': anime.rating,
                'status': watch_status.status,
                'status_display': watch_status.get_status_display(),
            })
        
        return Response({
            'count': paginator.count,
            'page': page,
            'limit': limit,
            'total_pages': paginator.num_pages,
            'results': anime_data
        })