# recommend_anime_view.py
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import F, FloatField, ExpressionWrapper,Q
from functools import reduce
import operator
from rest_framework import permissions
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication


from wangumi_app.models import Anime, Comment, WatchStatus, UserFollow
from django.db.models import Count, Avg

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

class ContactChangeRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = [JWTAuthentication]
    def get(self,request):
        user = request.user if request.user.is_authenticated else None
        try:
            page = int(request.GET.get("page", 1))
            limit = int(request.GET.get("limit", 20))
        except ValueError:
            return _build_error_response("page 和 limit 需要是正整数")

        if page <= 0 or limit <= 0:
            return _build_error_response("page 和 limit 需要是正整数")

        limit = min(limit, 100)
        source = request.GET.get('source', None)  # 可选：friend / interest / hot 或不选 
        if source in ("", None, "None"):  # 处理空字符串和None
            source = None
        
        #未登录用户只返回热门推荐
        if not user:
            return self._get_hot_only(page, limit)

        #优先从缓存获取推荐结果
        cache_key = f"recommend_{user.id}_{source}_{page}_{limit}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        recommendations = []
        active_weights = {'interest': 0, 'friend': 0, 'hot': 0}
       
        # ---------- 1. 好友推荐 ----------
        if source is None or source == "friend":
            friend_recs = self._get_friend_based(user)
            if friend_recs:
                active_weights["friend"] = BETA
                recommendations.extend(friend_recs)
        # ---------- 2. 兴趣推荐 ----------
        if source is None or source == "interest":
            interest_recs = self._get_interest_based(user)
            if interest_recs:
                active_weights["interest"] = ALPHA
                recommendations.extend(interest_recs)
        # ---------- 3. 热门推荐 ----------
        if source is None or source == "hot":
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
        # ========== 5. 分页 ==========
        paginator = Paginator(final_list, limit)
        page_obj = paginator.get_page(page)
        data = {
            "count": paginator.count,
            "page": page,
            "limit": limit,
            "results": list(page_obj.object_list)
        }

        cache.set(cache_key, data, 60 * 30)  # 缓存30分钟
        return Response(data)

    # ---------- 推荐算法实现部分 ----------
    def _get_interest_based(self, user):
        anime_ids = Comment.objects.filter(user=user, scope="ANIME").values_list("object_id", flat=True)
        if not anime_ids.exists() and not WatchStatus.objects.filter(user=user).exists():
            return []

        comment_tag_weights = {}
        for anime in Anime.objects.filter(id__in=anime_ids):
            if anime.genres:
                for genre in anime.genres :
                    comment_tag_weights[genre] = comment_tag_weights.get(genre, 0) + 5

        status_weight_map = {"WANT": 4, "WATCHING": 7, "FINISHED": 8}
        watch_tags = (
            WatchStatus.objects.filter(user=user)
            .values('anime__genres', 'status')
            .annotate(count=Count('id'))
        )

        watch_tag_weights = {}
        for w in watch_tags:
            tags = w['anime__genres'] or []
            if not isinstance(tags, list):  # 安全处理，确保是列表
                tags = []
            weight = status_weight_map.get(w['status'], 5)
            for tag in tags:
                watch_tag_weights[tag] = watch_tag_weights.get(tag, 0) + weight

        tag_weights = {}
        for tag, weight in comment_tag_weights.items():
            tag_weights[tag] = tag_weights.get(tag, 0) + weight
        for tag, weight in watch_tag_weights.items():
            tag_weights[tag] = tag_weights.get(tag, 0) + weight

        if not tag_weights:
            return []

        genre_queries = [Q(genres__contains=genre) for genre in tag_weights.keys()]
        combined_query = reduce(operator.or_, genre_queries)
        interest_based = Anime.objects.filter(combined_query)
        recs = []
        for anime in interest_based:
            score = 0
            if anime.genres:
                for genre in anime.genres:
                    score += tag_weights.get(genre, 0)
            anime_recommend_score = score * ALPHA
            recs.append({
                "id": anime.id,
                "title": anime.title,
                "rating": anime.rating,
                "reason": "兴趣相似",
                "cover_url": _resolve_cover_url(anime),
                "score": anime_recommend_score,
            })
        return recs

    def _get_friend_based(self, user):
        friends = UserFollow.objects.filter(follower=user).values_list('following', flat=True)
        if not friends.exists():
            return []

        friend_recent = (
            WatchStatus.objects.filter(user__in=friends)
            .values('anime')
            .annotate(freq=Count('id'))
            .order_by('-freq')
        )

        recs = []
        for item in friend_recent:
            anime = Anime.objects.filter(id=item['anime']).first()
            if anime:
                recs.append({
                    "id": anime.id,
                    "title": anime.title,
                    "reason": "好友在追",
                    "rating": anime.rating,
                    "cover_url": _resolve_cover_url(anime),
                    "score": BETA * item['freq']
                })
        return recs

    def _get_hot_based(self):
        hot_anime = Anime.objects.annotate(
            # 热度等于 rating+popularity
            hot_score=ExpressionWrapper(
                (F('popularity') / 1000.0) * 0.7 +
                (F('rating') / 10.0) * 0.3,
                output_field=FloatField()
            )
        ).order_by('-hot_score')[:50]
        recs = []
        for anime in hot_anime:
            recs.append({
                "id": anime.id,
                "title": anime.title,
                "cover_url": _resolve_cover_url(anime),
                "rating": anime.rating,
                "reason": "热门",
                "score": GAMMA * getattr(anime, 'hot_score', 0),
            })
        return recs

    def _get_hot_only(self, page, limit):
        """未登录用户：只显示热门"""
        hot_list = self._get_hot_based()
        paginator = Paginator(hot_list, limit)
        page_obj = paginator.get_page(page)
        data = {
            "count": paginator.count,
            "page": page,
            "limit": limit,
            "results": list(page_obj.object_list)
        }
        return Response(data)
