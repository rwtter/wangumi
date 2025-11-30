from django.http import JsonResponse
from django.core.paginator import Paginator
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from wangumi_app.models import Activity,User,UserFollow,UserProfile,Comment,Like,WatchStatus,Anime,PrivacySetting

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

"""
用户动态自动生成
"""
def create_activity(user, instance, action):
    content_type = ContentType.objects.get_for_model(instance.__class__)
    Activity.objects.create(
        user=user,
        content_type=content_type,
        object_id=instance.id,
        action=action
    )

"""
部分工具函数
"""
def _build_error_response(message: str, status: int = 400) -> JsonResponse:
    payload = {"code": 1, "message": message, "data": None}
    return JsonResponse(payload, status=status)

def is_following(viewer, owner):
    """检查viewer是否关注了owner"""
    return UserFollow.objects.filter(follower=viewer, following=owner).exists()

def is_mutual_follow(viewer, owner):
    """检查viewer和owner是否互相关注"""
    return (
        UserFollow.objects.filter(follower=viewer, following=owner).exists() and
        UserFollow.objects.filter(follower=owner, following=viewer).exists()
    )

def can_view_activity(viewer, owner):
    try:
        privacy_setting = PrivacySetting.objects.get(user=owner)
        privacy = privacy_setting.activities
    except PrivacySetting.DoesNotExist:
        # 如果没有隐私设置，默认为公开
        privacy = "public"

    if privacy == "public":
        return True
    if privacy == "self":
        return viewer == owner
    if privacy == "friends":
        return viewer and(viewer==owner or is_following(viewer, owner))
    if privacy == "mutual":
        return viewer and (viewer==owner or is_mutual_follow(viewer, owner))
    return False


class UserActivityView(APIView):
    """
    /api/user_activities/<user_id>/
    查询该用户发布的动态（评论、点赞、新增的追番等）。
    支持分页、隐私检查、按时间倒序排列。
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        user_id = request.GET.get("user_id")
        if not user_id:
            return JsonResponse({"code": 1, "message": "user_id不能为空", "data": None}, status=400)
    
        # 进行隐私可见性检查
        viewer = request.user if request.user.is_authenticated else None
        target_user = User.objects.filter(pk=user_id).first()
        if not target_user:
            return _build_error_response("用户不存在", status=404)

        if not can_view_activity(viewer, target_user):
            return JsonResponse({"detail": "该内容不公开"}, status=403)
    
        # 处理分页参数
        try:
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            return _build_error_response("page 和 limit 需要是正整数")

        if page <= 0 or limit <= 0:
            return _build_error_response("page 和 limit 需要是正整数")

        limit = min(limit, 100)

        # 查询动态
        queryset = Activity.objects.filter(user=target_user).order_by("-created_at")

        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)

        # 预加载关联对象，避免循环里发SQL
        comment_ct = ContentType.objects.get_for_model(Comment)
        watch_ct = ContentType.objects.get_for_model(WatchStatus)
        item_ct = ContentType.objects.get_for_model(Anime)
        like_ct = ContentType.objects.get_for_model(Like)
        
        comment_ids = [a.object_id for a in page_obj if a.content_type_id == comment_ct.id]
        watch_ids = [a.object_id for a in page_obj if a.content_type_id == watch_ct.id]
        item_ids = [a.object_id for a in page_obj if a.content_type_id == item_ct.id]
        like_ids = [a.object_id for a in page_obj if a.content_type_id == like_ct.id]
        
        comments = Comment.objects.filter(id__in=comment_ids)
        comment_map = {c.id: c for c in comments}
        
        watch_statuses = WatchStatus.objects.filter(id__in=watch_ids)
        watch_map = {w.id: w for w in watch_statuses}

        items = Anime.objects.filter(id__in=item_ids)
        item_map = {i.id: i for i in items}

        likes = Like.objects.filter(id__in=like_ids)
        like_map = {l.id: l for l in likes}

        # 序列化发送内容
        results = []
        for act in page_obj:
            target = None
            title = "[对象已删除]"

            print("Processing activity:", act.id, act.action)
            if act.action in ["创建了评论", "COMMENT"]:
                target = comment_map.get(act.object_id)
                if target:
                    title = target.content[:50]  # 前50字符展示
            elif act.action in ["WATCH", "新增追番"]:
                target = watch_map.get(act.object_id)
                if target and hasattr(target, "anime"):
                    title = target.anime.title
            elif act.action in ["ITEM", "新建了条目"]:
                target = item_map.get(act.object_id)
                if target:
                    title = target.title
            elif act.action in ["LIKE", "点赞了对象"]:
                target = like_map.get(act.object_id)
                if target:
                    if hasattr(target.comment, "content"):
                        title = target.comment.content[:50]

            results.append({
                "id": act.id,
                "action": act.action,
                "created_at": act.created_at,
                "target_id": act.object_id,
                "target_type": act.content_type.model,
                "target_title": title,
            })

        # 返回 JSON 响应
        response_payload = {
            "code": 0,
            "message": "success",
            "data": {
                "list": results,
                "pagination": {
                    "page": page_obj.number if paginator.count else page,
                    "limit": limit,
                    "total": paginator.count,
                    "pages": paginator.num_pages,
                },
            },
        }
        return JsonResponse(response_payload)

    def delete(self, request):
        """
        删除指定动态
        """
        activity_id = request.GET.get("activity_id")
        if not activity_id:
            return JsonResponse({"code": 1, "message": "activity_id不能为空", "data": None}, status=400)

        try:
            activity = Activity.objects.get(pk=activity_id, user=request.user)
        except Activity.DoesNotExist:
            return JsonResponse({"code": 1, "message": "动态不存在或无权限删除", "data": None}, status=404)

        activity.delete()
        return JsonResponse({"code": 0, "message": "动态删除成功", "data": None})
