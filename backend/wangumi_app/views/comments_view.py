import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import F,Count, Avg, Q
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from wangumi_app.models import Comment, Anime, Episode, Like, WatchStatus, Reply, Character, Person
from wangumi_app.views.user_activities_view import create_activity

@method_decorator(csrf_exempt, name='dispatch')
class CommentView(APIView):
    """评论功能接口 - 支持番剧、单集、条目评论"""

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

    def get(self, request):
        """获取评论列表"""
        try:
            # 获取查询参数
            scope = request.GET.get('scope')
            object_id = request.GET.get('object_id')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 50)
            order_by = request.GET.get('order_by', 'time_desc')
            min_score = request.GET.get('min_score')
            max_score = request.GET.get('max_score')

            # 验证必需参数
            if not scope or not object_id:
                return Response({
                    "code": 400,
                    "message": "scope和object_id参数不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证对象存在性
            target_object, object_info = self._get_target_object(scope, object_id)
            if not target_object:
                return Response({
                    "code": 404,
                    "message": f"{self._get_scope_display(scope)}不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 构建评论查询集
            content_type = ContentType.objects.get_for_model(target_object.__class__)
            comments_queryset = Comment.objects.filter(
                content_type=content_type,
                object_id=object_id,
                scope=scope
            ).select_related('user')

            # 评分过滤
            if min_score:
                comments_queryset = comments_queryset.filter(score__gte=min_score)
            if max_score:
                comments_queryset = comments_queryset.filter(score__lte=max_score)

            # 排序
            if order_by == 'time_asc':
                comments_queryset = comments_queryset.order_by('created_at')
            elif order_by == 'likes_desc':
                comments_queryset = comments_queryset.order_by('-likes', '-created_at')
            elif order_by == 'score_desc':
                comments_queryset = comments_queryset.order_by('-score', '-created_at')
            else:  # time_desc 默认
                comments_queryset = comments_queryset.order_by('-created_at')

            # 分页
            paginator = Paginator(comments_queryset, page_size)
            try:
                comments_page = paginator.page(page)
            except:
                comments_page = paginator.page(1)

            # 获取当前用户的点赞状态和追番状态（如果已登录）
            user_liked_comments = set()
            user_watch_status = None
            
            if request.user.is_authenticated:
                # 获取点赞状态
                user_liked_comments = set(
                    Like.objects.filter(
                        user=request.user,
                        comment__in=[c.id for c in comments_page],
                        is_active=True
                    ).values_list('comment_id', flat=True)
                )
                
                # 获取追番状态（如果是番剧）
                if scope == 'ANIME':
                    try:
                        watch_status = WatchStatus.objects.get(
                            user=request.user,
                            anime=target_object
                        )
                        user_watch_status = watch_status.status
                    except WatchStatus.DoesNotExist:
                        user_watch_status = None

            # 获取回复数量
            comment_ids = [comment.id for comment in comments_page]
            reply_counts = dict(
                Reply.objects.filter(review_id__in=comment_ids)
                .values('review_id')
                .annotate(count=Count('id'))
                .values_list('review_id', 'count')
            )

            # 构建评论数据
            comments_data = []
            for comment in comments_page:
                author_info = self._get_author_info(comment.user)
                is_current_user = request.user.is_authenticated and comment.user_id == request.user.id
                is_liked = comment.id in user_liked_comments if request.user.is_authenticated else False

                comments_data.append({
                    "comment_id": comment.id,
                    "score": comment.score,
                    "content": comment.content,
                    "author": author_info,
                    "likes_count": comment.likes,
                    "is_liked": is_liked,
                    "replies_count": reply_counts.get(comment.id, 0),
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "is_author": is_current_user,
                    "user_watch_status": user_watch_status if is_current_user else None
                })

            # 获取评分统计
            rating_stats = self._get_rating_stats(comments_queryset)

            response_data = {
                "scope": scope,
                "object_id": object_id,
                "object_info": {
                    **object_info,
                    "total_comments": paginator.count,
                    "average_rating": rating_stats['average']
                },
                "total_comments": paginator.count,
                "page": page,
                "page_size": page_size,
                "total_pages": paginator.num_pages,
                "comments": comments_data,
                "rating_stats": rating_stats
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

    def _get_rating_stats(self, comments_queryset):
        """获取评分统计信息"""
        try:
            # 计算平均分
            avg_result = comments_queryset.aggregate(avg_score=Avg('score'))
            average_rating = round(float(avg_result['avg_score'] or 0), 1)

            # 计算评分分布
            distribution = {str(i): 0 for i in range(1, 11)}
            score_counts = comments_queryset.values('score').annotate(count=Count('id'))
            
            for item in score_counts:
                distribution[str(item['score'])] = item['count']

            return {
                "average": average_rating,
                "distribution": distribution
            }
        except Exception as e:
            print(f"计算评分统计失败: {e}")
            return {
                "average": 0,
                "distribution": {str(i): 0 for i in range(1, 11)}
            }

    def _get_target_object(self, scope, object_id):
        """根据范围获取目标对象"""
        try:
            if scope == 'ANIME':
                anime = Anime.objects.get(id=object_id)
                return anime, {
                    "id": anime.id,
                    "title": anime.title,
                    "type": "ANIME",
                    "is_admin": anime.is_admin
                }
            elif scope == 'EPISODE':
                episode = Episode.objects.get(id=object_id)
                return episode, {
                    "id": episode.id,
                    "title": episode.title,
                    "anime_title": episode.anime.title,
                    "type": "EPISODE"
                }
            elif scope == 'ITEM':
                anime = Anime.objects.get(id=object_id, is_admin=False)
                return anime, {
                    "id": anime.id,
                    "title": anime.title,
                    "type": "ITEM",
                    "is_admin": False,
                    "created_by": anime.created_by.username if anime.created_by else None
                }
            elif scope == 'CHARACTER':
                character = Character.objects.get(id=object_id)
                return character, {
                    "id": character.id,
                    "name": character.name,
                    "type": "CHARACTER"
                }
            elif scope == 'PERSON':
                person = Person.objects.get(pers_id=object_id)
                return person, {
                    "id": person.pers_id,
                    "name": person.pers_name,
                    "type": "PERSON"
                }
        except (Anime.DoesNotExist, Episode.DoesNotExist, Character.DoesNotExist, Person.DoesNotExist) as e:
            print(f"获取目标对象失败: {e}")
            return None, None
        except Exception as e:
            print(f"获取目标对象时发生未知错误: {e}")
            return None, None
    
    def _get_scope_display(self, scope):
        """获取评论范围的中文显示"""
        scope_map = {
            'ANIME': '番剧',
            'EPISODE': '单集',
            'ITEM': '条目',
            'CHARACTER': '角色',
            'PERSON': '人物'
        }
        return scope_map.get(scope, '对象')

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
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        """发表或更新评论"""
        try:
            # 解析请求体
            data = json.loads(request.body)
            scope = data.get('scope')
            object_id = data.get('object_id')
            score = data.get('score')
            content = data.get('content', '').strip()

            # 参数验证
            validation_errors = self._validate_parameters(scope, object_id, score, content)
            if validation_errors:
                return Response({
                    "code": 400,
                    "message": "请求参数错误",
                    "errors": validation_errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证对象存在性并获取对象信息
            target_object, object_info = self._get_target_object(scope, object_id)
            if not target_object:
                return Response({
                    "code": 404,
                    "message": f"{self._get_scope_display(scope)}不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查是否已经评论过（同一用户对同一对象只能有一条评论）
            content_type = ContentType.objects.get_for_model(target_object.__class__)
            existing_comment = Comment.objects.filter(
                content_type=content_type,
                object_id=object_id,
                user=request.user,
                scope=scope
            ).first()

            is_update = existing_comment is not None
            heat_increased = False

            if existing_comment:
                # 更新现有评论
                update_fields = []
                if existing_comment.score != int(score):
                    existing_comment.score = int(score)
                    update_fields.append('score')
                if existing_comment.content != content:
                    existing_comment.content = content
                    update_fields.append('content')
                
                if update_fields:
                    existing_comment.save(update_fields=update_fields)
                
                comment = existing_comment
                message = "评论更新成功"
            else:
                # 创建新评论
                comment = Comment.objects.create(
                    content_type=content_type,
                    object_id=object_id,
                    user=request.user,
                    score=int(score),
                    content=content,
                    scope=scope
                )
                heat_increased = self._increase_heat(target_object, scope)
                message = "评论发表成功"
                create_activity(request.user, comment, "创建了评论")  # 创建动态记录

            # 更新对象的评分
            self._update_object_rating(comment)

            # 准备响应数据
            response_data = {
                "comment_id": comment.id,
                "scope": scope,
                "object_id": object_id,
                "score": comment.score,
                "content": comment.content,
                "author": {
                    "user_id": request.user.id,
                    "username": request.user.username,
                    "avatar": self._get_user_avatar(request.user)
                },
                "object_info": object_info,
                "likes_count": comment.likes,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "updated_at": comment.created_at.isoformat() if comment.created_at else None,
                "heat_increased": heat_increased,
                "is_update": is_update,
                "message": message
            }

            return Response({
                "code": 200 if is_update else 201,
                "message": message,
                "data": response_data
            }, status=status.HTTP_200_OK if is_update else status.HTTP_201_CREATED)

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

    def _validate_parameters(self, scope, object_id, score, content):
        """验证请求参数"""
        errors = {}

        # 验证评论范围
        valid_scopes = [choice[0] for choice in Comment.COMMENT_SCOPE]
        if not scope:
            errors['scope'] = ['评论范围不能为空']
        elif scope not in valid_scopes:
            errors['scope'] = [f'评论范围必须是以下之一: {", ".join(valid_scopes)}']

        # 验证对象ID
        if not object_id:
            errors['object_id'] = ['对象ID不能为空']
        else:
            try:
                object_id = int(object_id)
            except (ValueError, TypeError):
                errors['object_id'] = ['对象ID必须是整数']

        # 验证评分
        if score is None:
            errors['score'] = ['评分不能为空']
        else:
            try:
                score = float(score)
                if score < 1 or score > 10:
                    errors['score'] = ['评分必须在1-10之间']
                elif (score * 2) % 1 != 0:
                    errors['score'] = ['评分必须是0.5的倍数（支持半星评分）']
            except (ValueError, TypeError):
                errors['score'] = ['评分必须是数字']

        # 验证评论内容
        if not content:
            errors['content'] = ['评论内容不能为空']
        elif len(content) > 500:
            errors['content'] = ['评论内容不能超过500字符']

        return errors

    def _increase_heat(self, target_object, scope):
        """增加对象热度值"""
        try:
            if hasattr(target_object, 'popularity'):
                target_object.popularity = F('popularity') + 1
                target_object.save(update_fields=['popularity'])
                target_object.refresh_from_db(fields=['popularity'])
                return True
            elif hasattr(target_object, 'heat'):
                target_object.heat = F('heat') + 1
                target_object.save(update_fields=['heat'])
                target_object.refresh_from_db(fields=['heat'])
                return True
        except Exception as e:
            print(f"更新热度失败: {e}")
        return False

    def _update_rating(self, target_object, content_type, object_id):
        """更新平均评分"""
        try:
            if hasattr(target_object, 'rating'):
                from django.db.models import Avg
                avg_result = Comment.objects.filter(
                    content_type=content_type,
                    object_id=object_id
                ).aggregate(avg_score=Avg('score'))
                
                new_rating = float(avg_result['avg_score'] or 0.0)
                target_object.rating = new_rating
                target_object.save(update_fields=['rating'])
        except Exception as e:
            print(f"更新评分失败: {e}")

    # 在 CommentView 类中添加 put 方法用于更新评论
    @transaction.atomic
    def put(self, request):
        """更新评论"""
        try:
            # 解析请求体
            data = json.loads(request.body)
            comment_id = data.get('comment_id')
            score = data.get('score')
            content = data.get('content', '').strip()

            # 参数验证
            if not comment_id:
                return Response({
                    "code": 400,
                    "message": "comment_id参数不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证评分
            if score is not None:
                try:
                    score = float(score)
                    if score < 1 or score > 10:
                        return Response({
                            "code": 400,
                            "message": "评分必须在1-10之间",
                            "data": None
                        }, status=status.HTTP_400_BAD_REQUEST)
                    if (score * 2) % 1 != 0:
                        return Response({
                            "code": 400,
                            "message": "评分必须支持半星制（如8.0, 8.5等）",
                            "data": None
                        }, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({
                        "code": 400,
                        "message": "评分必须是数字",
                        "data": None
                    }, status=status.HTTP_400_BAD_REQUEST)

            # 验证评论内容长度
            if content and len(content) > 500:
                return Response({
                    "code": 400,
                    "message": "评论内容不能超过500字符",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取评论对象
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查权限
            if comment.user_id != request.user.id:
                return Response({
                    "code": 403,
                    "message": "只能修改自己的评论",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)

            # 更新评论
            update_fields = []
            if score is not None:
                comment.score = int(score)  # 转换为整数存储
                update_fields.append('score')
            if content is not None:
                comment.content = content
                update_fields.append('content')
            
            if update_fields:
                comment.save(update_fields=update_fields)

            # 更新相关对象的评分
            self._update_object_rating(comment)

            # 准备响应数据
            response_data = {
                "comment_id": comment.id,
                "scope": comment.scope,
                "object_id": comment.object_id,
                "score": comment.score,
                "content": comment.content,
                "updated_at": comment.created_at.isoformat() if comment.created_at else None,
                "message": "评论更新成功"
            }

            return Response({
                "code": 200,
                "message": "评论更新成功",
                "data": response_data
            })

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

    def _update_object_rating(self, comment):
        """更新相关对象的评分"""
        try:
            # 获取评论对应的对象
            target_object = comment.content_object
            if not target_object:
                return

            # 重新计算平均评分
            content_type = ContentType.objects.get_for_model(target_object.__class__)
            avg_result = Comment.objects.filter(
                content_type=content_type,
                object_id=comment.object_id
            ).aggregate(avg_score=Avg('score'))
            
            new_rating = float(avg_result['avg_score'] or 0.0)
            
            # 更新对象的评分
            if hasattr(target_object, 'rating'):
                target_object.rating = new_rating
                target_object.save(update_fields=['rating'])
                
        except Exception as e:
            print(f"更新对象评分失败: {e}")