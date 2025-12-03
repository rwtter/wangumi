import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import Comment, Reply, Like

@method_decorator(csrf_exempt, name='dispatch')
class ReplyView(APIView):
    """回复功能接口 - 创建回复和获取回复列表"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """根据请求方法动态设置权限"""
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_authentication_classes(self):
        """根据请求方法动态设置认证"""
        if self.request.method == 'GET':
            self.authentication_classes = []
        else:
            self.authentication_classes = [JWTAuthentication]
        return super().get_authentication_classes()

    def get(self, request, comment_id):
        """获取特定评论的回复列表"""
        try:
            # 验证评论是否存在
            try:
                parent_comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 获取查询参数
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 50)
            order_by = request.GET.get('order_by', 'time_desc')

            # 构建回复查询集
            replies_queryset = Reply.objects.filter(review=parent_comment).select_related('user')

            # 排序
            if order_by == 'time_asc':
                replies_queryset = replies_queryset.order_by('created_at')
            elif order_by == 'likes_desc':
                # 如果Reply模型有likes字段，可以按点赞数排序
                if hasattr(Reply, 'likes'):
                    replies_queryset = replies_queryset.order_by('-likes', '-created_at')
                else:
                    replies_queryset = replies_queryset.order_by('-created_at')
            else:  # time_desc 默认
                replies_queryset = replies_queryset.order_by('-created_at')

            # 分页
            paginator = Paginator(replies_queryset, page_size)
            try:
                replies_page = paginator.page(page)
            except:
                replies_page = paginator.page(1)

            # 获取当前用户的点赞状态（如果已登录）
            user_liked_replies = set()
            if request.user.is_authenticated:
                # 注意：这里需要根据你的Like模型结构调整
                # 如果Like关联的是Comment，可能需要调整查询
                user_liked_replies = set(
                    Like.objects.filter(
                        user=request.user,
                        comment_id__in=[r.id for r in replies_page],
                        is_active=True
                    ).values_list('comment_id', flat=True)
                )

            # 构建回复数据
            replies_data = []
            for reply in replies_page:
                author_info = self._get_author_info(reply.user)
                is_current_user = request.user.is_authenticated and reply.user_id == request.user.id
                
                # 检查是否点赞（根据你的Like模型结构调整）
                is_liked = reply.id in user_liked_replies if request.user.is_authenticated else False

                replies_data.append({
                    "reply_id": reply.id,
                    "content": reply.content,
                    "author": author_info,
                    "likes_count": getattr(reply, 'likes', 0),  # 如果Reply模型有likes字段
                    "is_liked": is_liked,
                    "created_at": reply.created_at.isoformat() if reply.created_at else None,
                    "is_author": is_current_user
                })

            response_data = {
                "comment_id": parent_comment.id,
                "parent_comment": {
                    "content": parent_comment.content,
                    "author": self._get_author_info(parent_comment.user)
                },
                "total_replies": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "replies": replies_data
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

    def _get_author_info(self, user):
        """获取作者信息"""
        try:
            level = getattr(user, 'level', 1) if hasattr(user, 'level') else 1
            is_verified = getattr(user, 'is_verified', False) if hasattr(user, 'is_verified') else False
            
            return {
                "user_id": user.id,
                "username": user.username,
                "avatar": self._get_user_avatar(user),
                "level": level,
                "is_verified": is_verified
            }
        except:
            return {
                "user_id": user.id,
                "username": user.username,
                "avatar": "/avatars/default.jpg",
                "level": 1,
                "is_verified": False
            }

    def _get_user_avatar(self, user):
        """获取用户头像URL"""
        try:
            if hasattr(user, 'userprofile') and user.userprofile.avatar:
                return user.userprofile.avatar.url
        except:
            pass
        return "/avatars/default.jpg"

    @transaction.atomic
    def post(self, request, comment_id):
        """创建回复（需要认证）"""
        try:
            # 解析请求体
            data = json.loads(request.body)
            content = data.get('content', '').strip()

            # 参数验证 - 内容不能为空
            if not content:
                return Response({
                    "code": 400,
                    "message": "回复内容不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证内容长度
            if len(content) > 500:
                return Response({
                    "code": 400,
                    "message": "回复内容不能超过500字符",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证评论是否存在
            try:
                parent_comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 可选：检查是否回复自己的评论
            # if parent_comment.user_id == request.user.id:
            #     return Response({
            #         "code": 400,
            #         "message": "不能回复自己的评论",
            #         "data": None
            #     }, status=status.HTTP_400_BAD_REQUEST)

            # 创建回复记录
            reply = Reply.objects.create(
                review=parent_comment,
                user=request.user,
                content=content
            )

            # 更新父评论的回复计数（如果模型有这个字段）
            if hasattr(parent_comment, 'comments'):
                parent_comment.comments = parent_comment.comments + 1 if parent_comment.comments else 1
                parent_comment.save(update_fields=['comments'])

            # 准备响应数据
            response_data = {
                "reply_id": reply.id,
                "comment_id": parent_comment.id,
                "content": reply.content,
                "author": {
                    "user_id": request.user.id,
                    "username": request.user.username,
                    "avatar": self._get_user_avatar(request.user)
                },
                "parent_author": {
                    "user_id": parent_comment.user.id,
                    "username": parent_comment.user.username
                },
                "created_at": reply.created_at.isoformat() if reply.created_at else None,
                "likes_count": 0
            }

            return Response({
                "code": 201,
                "message": "回复成功",
                "data": response_data
            }, status=status.HTTP_201_CREATED)

        except json.JSONDecodeError:
            return Response({
                "code": 400,
                "message": "请求体格式错误",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)