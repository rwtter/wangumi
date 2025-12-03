from django.db import transaction
from django.db.models import Avg, F
from django.http import JsonResponse
from django.contrib.contenttypes.models import ContentType

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import Anime, Comment
from wangumi_app.views.user_activities_view import create_activity


def _json_ok(data=None):
    return JsonResponse({"code": 200, "message": "success", "data": data or {}}, json_dumps_params={'ensure_ascii': False})

def _json_error(status: int, message: str, code: int = None):
    return JsonResponse({"code": code or status, "message": message, "data": None}, status=status, json_dumps_params={'ensure_ascii': False})

class CreateAnimeReviewView(APIView):
    """
    创建或更新番剧评价接口
    UC12-1: 番剧评价接口定义与输入校验
    UC12-2: 实现评论保存逻辑（支持同一用户多次评价时更新而非插入）
    UC12-3: 更新番剧评价与热度
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        body = request.data or {}
        anime_id = body.get('animeId') or body.get('anime_id')
        rating = body.get('score')or body.get('rating')
        comment_text = body.get('comment') or ''

        # UC12-1: 输入校验
        if not anime_id:
            return _json_error(400, 'anime_id不能为空', 400)

        # 校验番剧存在性
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return _json_error(404, '番剧不存在', 404)

        # 校验评分格式（支持半星制：1.0-10.0，步长0.5）
        if rating is None:
            return _json_error(400, 'rating不能为空', 400)

        try:
            rating = float(rating)
        except Exception:
            return _json_error(400, '评分必须是数字', 400)

        if rating < 1.0 or rating > 10.0:
            return _json_error(400, '评分必须在1-10之间', 400)

        # 检查是否为有效的半星评分（1.0, 1.5, 2.0, ..., 10.0）
        if (rating * 2) % 1 != 0:
            return _json_error(400, '评分必须支持半星制（如8.0, 8.5等）', 400)

        # 校验评论长度
        if len(comment_text) > 500:
            return _json_error(400, '评论内容不能超过500字符', 400)

        # UC12-2: 实现评论保存逻辑（存在则更新，不存在则创建）
        ct = ContentType.objects.get_for_model(Anime)
        existing_review = Comment.objects.filter(content_type=ct, object_id=anime.id, user=request.user).first()

        if existing_review:
            # 更新已有评价
            is_new_rating = False
            if existing_review.score != rating:
                existing_review.score = rating
                is_new_rating = True

            if comment_text is not None:
                existing_review.content = comment_text

            existing_review.save(update_fields=['score', 'content', 'updated_at'] if hasattr(existing_review, 'updated_at') else ['score', 'content'])
            review = existing_review
        else:
            # 创建新评价
            review = Comment.objects.create(
                content_type=ct,
                object_id=anime.id,
                user=request.user,
                score=rating,
                content=comment_text
            )
            is_new_rating = True

            create_activity(request.user, review, "创建了评论")# 创建动态记录

        # UC12-3: 更新番剧评价与热度
        # 重新计算评分
        agg = Comment.objects.filter(content_type=ct, object_id=anime.id).aggregate(avg=Avg('score'))
        new_avg = float(agg['avg'] or 0.0)

        # 更新番剧评分
        if is_new_rating and not existing_review:
            # 首次创建评价时增加热度
            Anime.objects.filter(id=anime.id).update(rating=new_avg, popularity=F('popularity') + 1)
        else:
            # 更新评价时只更新评分
            Anime.objects.filter(id=anime.id).update(rating=new_avg)

        anime.refresh_from_db(fields=['rating', 'popularity'])

        return _json_ok({
            "user_id": request.user.id,
            "reviewId": review.id,
            "animeId": anime.id,
            "score": anime.rating,
            "heat": anime.popularity,
            "message": "评价提交成功" if not existing_review else "评价更新成功"
        })


class GetAnimeReviewView(APIView):
    """
    获取用户番剧评价接口
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        anime_id = request.GET.get('anime_id')

        if not anime_id:
            return _json_error(400, 'anime_id参数不能为空', 400)

        try:
            anime_id = int(anime_id)
        except ValueError:
            return _json_error(400, 'anime_id必须是整数', 400)

        # 校验番剧存在性
        try:
            anime = Anime.objects.get(id=anime_id)
        except Anime.DoesNotExist:
            return _json_error(404, '番剧不存在', 404)

        # 查询用户评价
        ct = ContentType.objects.get_for_model(Anime)
        review = Comment.objects.filter(content_type=ct, object_id=anime.id, user=request.user).first()

        if not review:
            return _json_ok({
            "user_id": request.user.id,
            "animeId": anime.id,
            "animeTitle": anime.title,
            "hasReview": False,  # 新增字段，明确表示没有评价
            "score": None,
            "comment": None,
            "reviewId": None,
            "createdAt": None,
            "updatedAt": None
        })

        return _json_ok({
            "user_id": request.user.id,
            "reviewId": review.id,
            "animeId": anime.id,
            "animeTitle": anime.title,
            "score": review.score,
            "comment": review.content,
            "createdAt": review.created_at.isoformat() if review.created_at else None,
            "updatedAt": review.updated_at.isoformat() if hasattr(review, 'updated_at') and review.updated_at else None
        })

class UpdateReviewView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, review_id: int):
        body = request.data or {}
        score = body.get('score')
        comment_text = body.get('comment')

        try:
            score = int(score)
        except Exception:
            return _json_error(400, 'score must be integer in [1,10]')
        if score < 1 or score > 10:
            return _json_error(400, 'score must be integer in [1,10]')

        try:
            review = Comment.objects.select_for_update().get(id=review_id)
        except Comment.DoesNotExist:
            return _json_error(404, 'review not found')

        if review.user_id != request.user.id:
            return _json_error(403, 'cannot edit other\'s review')

        # 更新评论
        review.score = score
        if comment_text is not None:
            review.content = comment_text
        review.save(update_fields=['score', 'content', 'updated_at'] if hasattr(review, 'updated_at') else ['score', 'content'])

        # 重算评分（热度不变）
        ct = ContentType.objects.get_for_model(Anime)
        agg = Comment.objects.filter(content_type=ct, object_id=review.object_id).aggregate(avg=Avg('score'))
        new_avg = float(agg['avg'] or 0.0)
        Anime.objects.filter(id=review.object_id).update(rating=new_avg)

        anime = Anime.objects.get(id=review.object_id)
        return _json_ok({
            "user_id": request.user.id,
            "reviewId": review.id,
            "animeId": anime.id,
            "score": anime.rating,
            "heat": anime.popularity,
        })
        
        
