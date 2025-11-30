import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from wangumi_app.models import Comment, Like
from wangumi_app.views.user_activities_view import create_activity

@method_decorator(csrf_exempt, name='dispatch')
class LikeView(APIView):
    """点赞功能接口 - 对评论进行点赞/取消点赞"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, comment_id):
        """点赞评论"""
        try:
            # 验证评论是否存在
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查是否已经点赞过
            existing_like = Like.objects.filter(
                user=request.user,
                comment=comment,
                is_active=True
            ).first()

            if existing_like:
                return Response({
                    "code": 400,
                    "message": "您已经点赞过该内容",
                    "data": {
                        "existing_like_id": existing_like.id,
                        "liked_at": existing_like.created_at.isoformat() if existing_like.created_at else None
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # 检查是否有已存在的inactive记录，如果有则重新激活
            inactive_like = Like.objects.filter(
                user=request.user,
                comment=comment,
                is_active=False
            ).first()

            if inactive_like:
                # 重新激活现有的点赞记录
                inactive_like.is_active = True
                inactive_like.save(update_fields=['is_active'])
                like = inactive_like
            else:
                # 创建新的点赞记录
                like = Like.objects.create(
                    user=request.user,
                    comment=comment,
                    is_active=True
                )
                create_activity(request.user, like, "点赞了对象")# 记录点赞动态

            # 更新评论的点赞数
            comment.likes = F('likes') + 1
            comment.save(update_fields=['likes'])
            comment.refresh_from_db(fields=['likes'])


            # 准备响应数据
            response_data = {
                "comment_id": comment.id,
                "likes_count": comment.likes,
                "is_liked": True,
                "action": "liked",
                "like_id": like.id
            }

            return Response({
                "code": 200,
                "message": "点赞成功",
                "data": response_data
            })

        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def delete(self, request, comment_id):
        """取消点赞"""
        try:
            # 验证评论是否存在
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 查找点赞记录
            existing_like = Like.objects.filter(
                user=request.user,
                comment=comment,
                is_active=True
            ).first()

            if not existing_like:
                return Response({
                    "code": 400,
                    "message": "您还未点赞该内容",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 软删除点赞记录（设置 is_active=False）
            existing_like.is_active = False
            existing_like.save(update_fields=['is_active'])

            # 更新评论的点赞数（确保不会减到负数）
            if comment.likes > 0:
                comment.likes = F('likes') - 1
                comment.save(update_fields=['likes'])
                comment.refresh_from_db(fields=['likes'])

            # 准备响应数据
            response_data = {
                "comment_id": comment.id,
                "likes_count": comment.likes,
                "is_liked": False,
                "action": "unliked"
            }

            return Response({
                "code": 200,
                "message": "取消点赞成功",
                "data": response_data
            })

        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, comment_id):
        """获取当前用户对该评论的点赞状态"""
        try:
            # 验证评论是否存在
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 查询用户是否已经点赞
            existing_like = Like.objects.filter(
                user=request.user,
                comment=comment,
                is_active=True
            ).first()

            response_data = {
                "comment_id": comment.id,
                "likes_count": comment.likes,
                "is_liked": existing_like is not None,
                "user_like_id": existing_like.id if existing_like else None
            }

            return Response({
                "code": 200,
                "message": "success",
                "data": response_data
            })

        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)