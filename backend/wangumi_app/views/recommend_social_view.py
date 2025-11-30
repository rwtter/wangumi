import random
from django.db.models import Count, Q, F, FloatField, ExpressionWrapper
from django.core.paginator import Paginator
from django.templatetags.static import static

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse
from functools import reduce
import operator

from wangumi_app.models import UserFollow, WatchStatus, Anime, Comment, Like, Reply
from django.contrib.auth import get_user_model

User = get_user_model()

ALPHA = 0.5   # 兴趣相似度权重
BETA = 0.3    # 好友行为权重
GAMMA = 0.2   # 热度权重

def _build_error_response(message: str, status: int = 400) -> JsonResponse:
    payload = {"code": 1, "message": message, "data": None}
    return JsonResponse(payload, status=status, json_dumps_params={'ensure_ascii': False})

def _resolve_cover_url(anime) -> str:
    cover_image = getattr(anime, "cover_image", None)
    if cover_image:
        raw_name = getattr(cover_image, "name", "") or ""
        try:
            url = cover_image.url
        except (ValueError, AttributeError):
            url = raw_name
        if url.startswith("/media/http") and raw_name.startswith(("http://", "https://")):
            return raw_name
        if url:
            return url
    cover_url = getattr(anime, "cover_url", "") or ""
    return cover_url

def _resolve_avatar_url(user) -> str:
    try:
        userP = user.userprofile
        if userP.avatar:
            return userP.avatar.url
    except (AttributeError, ValueError):
        pass
    
    # 返回默认头像路径
    return "default-avatar.png"  # 默认头像存放在/media/default-avatar.png

class UserRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        user = request.user
        
        try:
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            return Response({"detail": "page 和 limit 需要是整数"}, status=400)

        if page <= 0 or limit <= 0:
            return Response({"detail": "page 和 limit 必须是正整数"}, status=400)

        limit = min(limit, 100)

        # 1. 获取自己关注的用户
        following_ids = UserFollow.objects.filter(follower=user).values_list("following", flat=True)

        # 2. 获取所有用户中排除：自己 + 已关注
        candidates = User.objects.exclude(id=user.id).exclude(id__in=following_ids)

        # 3. 统计共同追番数
        user_watch_ids = set(
            WatchStatus.objects
            .filter(user=user)
            .values_list("anime_id", flat=True)
        )

        # 用 annotate 做简易统计
        candidates = candidates.annotate(
            mutual_watch_count=Count(
                "watchstatus__anime",
                filter=Q(watchstatus__anime_id__in=user_watch_ids)
            )
        )

        # 4. 排序：共同追番数 + 随机
        candidates = list(candidates)
        random.shuffle(candidates)   # 外层打乱
        candidates.sort(key=lambda u: u.mutual_watch_count, reverse=True)

        # 5. 分页
        paginator = PageNumberPagination()
        paginator.page_size = limit
        page_obj = paginator.paginate_queryset(candidates, request)
        # 6. 返回字段：包括 mutual_watch_count
        data = [
            {
                "id": u.id,
                "username": u.username,
                "avatar": _resolve_avatar_url(u),
                "mutual_watch_count": u.mutual_watch_count,
            }
            for u in page_obj
        ]

        return paginator.get_paginated_response(data)


class recommendItemItemRecommendationView(APIView):
    permission_classes = []

    def get(self, request):
        user = request.user if request.user.is_authenticated else None

        try:
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            return _build_error_response("page 和 limit 需要是正整数")

        if page <= 0 or limit <= 0:
            return _build_error_response("page 和 limit 需要是正整数")

        limit = min(limit, 100)

        # 未登录用户只返回热门推荐
        if not user:
            return self._get_hot_only(page, limit)

        recommendations = []
        active_weights = {'interest': 0, 'friend': 0, 'hot': 0}

        # ---------- 1. 好友推荐 ----------
        friend_recs = self._get_friend_based(user)
        if friend_recs:
            active_weights["friend"] = BETA
            recommendations.extend(friend_recs)

        # ---------- 2. 兴趣推荐 ----------
        interest_recs = self._get_interest_based(user)
        if interest_recs:
            active_weights["interest"] = ALPHA
            recommendations.extend(interest_recs)

        # ---------- 3. 热门推荐 ----------
        hot_recs = self._get_hot_based()
        if hot_recs:
            active_weights["hot"] = GAMMA
            recommendations.extend(hot_recs)

        # 若缺乏部分数据，动态调整有效权重
        total_weight = sum(active_weights.values()) or 1
        for r in recommendations:
            # 重新按比例归一化分值
            r["score"] = r["score"] / total_weight

        # ---------- 4. 去重 + 排序 ----------
        seen = {}
        for r in recommendations:
            if r["id"] in seen:
                seen[r["id"]]["score"] += r["score"]
            else:
                seen[r["id"]] = r
        final_list = sorted(seen.values(), key=lambda x: x["score"], reverse=True)

        # ---------- 5. 分页 ----------
        paginator = Paginator(final_list, limit)
        page_obj = paginator.get_page(page)
        data = {
            "code": 0,
            "message": "success",
            "data": {
                "count": paginator.count,
                "page": page,
                "limit": limit,
                "results": list(page_obj.object_list)
            }
        }
        return Response(data)

    def _get_interest_based(self, user):
        # 获取用户评论过的条目（确保是条目，不是番剧）
        item_comments = Comment.objects.filter(
            user=user,
            scope="ITEM"
        ).values_list("object_id", flat=True)

        # 进一步确认这些 object_id 对应的是条目（is_admin=False）
        item_ids = Anime.objects.filter(
            id__in=item_comments,
            is_admin=False
        ).values_list("id", flat=True)

        # 获取用户点赞过的条目（确保是条目，不是番剧）
        liked_item_comments = Comment.objects.filter(
            like__user=user,
            like__is_active=True,
            scope="ITEM"
        ).values_list("id", flat=True)

        liked_item_ids = Anime.objects.filter(
            id__in=liked_item_comments,
            is_admin=False
        ).values_list("id", flat=True)

        # 获取用户回复过的条目（确保是条目，不是番剧）
        replied_item_comments = Comment.objects.filter(
            reply__user=user,
            scope="ITEM"
        ).values_list("id", flat=True)

        replied_item_ids = Anime.objects.filter(
            id__in=replied_item_comments,
            is_admin=False
        ).values_list("id", flat=True)

        # 合并用户行为数据
        all_item_ids = set(item_ids) | set(liked_item_ids) | set(replied_item_ids)

        if not all_item_ids:
            return []

        # 基于标签分析用户兴趣
        tag_weights = {}
        for item in Anime.objects.filter(id__in=all_item_ids, is_admin=False):
            if item.genres:
                for genre in item.genres:
                    # 评论权重
                    if item.id in item_ids:
                        tag_weights[genre] = tag_weights.get(genre, 0) + 8
                    # 点赞权重
                    if item.id in liked_item_ids:
                        tag_weights[genre] = tag_weights.get(genre, 0) + 5
                    # 回复权重
                    if item.id in replied_item_ids:
                        tag_weights[genre] = tag_weights.get(genre, 0) + 6

        if not tag_weights:
            return []

        # 基于标签权重推荐相似条目
        genre_queries = [Q(genres__contains=genre) for genre in tag_weights.keys()]
        combined_query = reduce(operator.or_, genre_queries)

        interest_based = Anime.objects.filter(
            combined_query,
            is_admin=False
        )

        recs = []
        for item in interest_based:
            score = 0
            if item.genres:
                for genre in item.genres:
                    score += tag_weights.get(genre, 0)
            item_recommend_score = score * ALPHA
            recs.append({
                "id": item.id,
                "title": item.title,
                "popularity": item.popularity,
                "cover_image": _resolve_cover_url(item),
                "score": item_recommend_score,
            })
        return recs

    def _get_friend_based(self, user):
        # 获取关注的好友
        friends = UserFollow.objects.filter(follower=user).values_list('following', flat=True)
        if not friends.exists():
            return []

        # 统计好友对条目的交互行为（确保是条目，不是番剧）

        # 好友评论过的条目
        friend_comments = Comment.objects.filter(
            user__in=friends,
            scope="ITEM"
        ).values('object_id').annotate(freq=Count('id'))

        # 好友点赞过的条目
        friend_likes = Like.objects.filter(
            user__in=friends,
            is_active=True,
            comment__scope="ITEM"
        ).values('comment__object_id').annotate(freq=Count('id'))

        # 好友回复过的条目
        friend_replies = Reply.objects.filter(
            user__in=friends,
            review__scope="ITEM"
        ).values('review__object_id').annotate(freq=Count('id'))

        # 合并好友行为数据，并过滤出只针对条目的交互
        item_activity = {}

        # 处理评论数据（确保是条目）
        comment_item_ids = [c['object_id'] for c in friend_comments]
        valid_comment_items = Anime.objects.filter(id__in=comment_item_ids, is_admin=False).values_list('id', flat=True)

        for comment in friend_comments:
            if comment['object_id'] in valid_comment_items:
                item_activity[comment['object_id']] = item_activity.get(comment['object_id'], 0) + comment['freq'] * 3

        # 处理点赞数据（确保是条目）
        like_item_ids = [l['comment__object_id'] for l in friend_likes]
        valid_like_items = Anime.objects.filter(id__in=like_item_ids, is_admin=False).values_list('id', flat=True)

        for like in friend_likes:
            item_id = like['comment__object_id']
            if item_id in valid_like_items:
                item_activity[item_id] = item_activity.get(item_id, 0) + like['freq'] * 2

        # 处理回复数据（确保是条目）
        reply_item_ids = [r['review__object_id'] for r in friend_replies]
        valid_reply_items = Anime.objects.filter(id__in=reply_item_ids, is_admin=False).values_list('id', flat=True)

        for reply in friend_replies:
            item_id = reply['review__object_id']
            if item_id in valid_reply_items:
                item_activity[item_id] = item_activity.get(item_id, 0) + reply['freq'] * 4

        recs = []
        for item_id, activity_score in item_activity.items():
            item = Anime.objects.filter(id=item_id, is_admin=False).first()
            if item:
                recs.append({
                    "id": item.id,
                    "title": item.title,
                    "popularity": item.popularity,
                    "cover_image": _resolve_cover_url(item),
                    "score": BETA * activity_score,
                })
        return recs

    def _get_hot_based(self):
        # 基于热度推荐条目
        hot_items = Anime.objects.filter(is_admin=False).annotate(
            hot_score=ExpressionWrapper(
                (F('popularity') / 1000.0) * 0.7 +
                (F('rating') / 10.0) * 0.3,
                output_field=FloatField()
            )
        ).order_by('-hot_score')[:50]

        recs = []
        for item in hot_items:
            recs.append({
                "id": item.id,
                "title": item.title,
                "popularity": item.popularity,
                "cover_image":  _resolve_cover_url(item),
                "score": GAMMA * getattr(item, 'hot_score', 0),
            })
        return recs

    def _get_hot_only(self, page, limit):
        """未登录用户：只显示热门条目"""
        hot_list = self._get_hot_based()
        paginator = Paginator(hot_list, limit)
        page_obj = paginator.get_page(page)
        data = {
            "code": 0,
            "message": "success",
            "data": {
                "count": paginator.count,
                "page": page,
                "limit": limit,
                "results": list(page_obj.object_list)
            }
        }
        return Response(data)
