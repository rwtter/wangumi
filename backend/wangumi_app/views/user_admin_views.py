import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from wangumi_app.models import User, UserBanLog, AdminLog, Comment, Reply, Anime, Report, UserProfile, PrivacySetting
from wangumi_app.views.report_admin_views import IsAdminUser

@method_decorator(csrf_exempt, name='dispatch')
class UserListStatusView(APIView):
    """获取所有用户状态列表"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # 获取查询参数
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 50)
            search = request.GET.get('search', '')
            status_filter = request.GET.get('status', '')
            order_by = request.GET.get('order_by', '-date_joined')

            # 构建查询条件
            queryset = User.objects.all().select_related('userprofile')
            
            # 搜索条件
            if search:
                queryset = queryset.filter(
                    Q(username__icontains=search) |
                    Q(email__icontains=search) |
                    Q(userprofile__nickname__icontains=search)
                )
            
            # 状态筛选
            if status_filter == 'active':
                queryset = queryset.filter(is_active=True)
            elif status_filter == 'banned':
                queryset = queryset.filter(is_active=False)
            
            # 排序
            if order_by in ['username', '-username', 'date_joined', '-date_joined', 'last_login', '-last_login']:
                queryset = queryset.order_by(order_by)
            else:
                queryset = queryset.order_by('-date_joined')

            # 分页
            paginator = Paginator(queryset, page_size)
            try:
                users_page = paginator.page(page)
            except:
                users_page = paginator.page(1)

            # 构建用户数据
            users_data = []
            for user in users_page:
                # 获取用户资料
                profile_data = self._get_user_profile(user)
                
                # 获取用户统计数据
                stats = self._get_user_stats(user)
                
                # 获取最近的封禁记录
                recent_ban_log = UserBanLog.objects.filter(user=user, action='BAN').order_by('-operated_at').first()
                
                users_data.append({
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "status": "正常" if user.is_active else "已封禁",
                    "profile": profile_data,
                    "date_joined": user.date_joined.isoformat() if user.date_joined else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "stats": stats,
                    "recent_ban_info": {
                        "reason": recent_ban_log.reason if recent_ban_log else None,
                        "banned_at": recent_ban_log.operated_at.isoformat() if recent_ban_log else None,
                        "banned_by": recent_ban_log.operated_by.username if recent_ban_log else None
                    } if not user.is_active and recent_ban_log else None
                })

            response_data = {
                "users": users_data,
                "pagination": {
                    "total": paginator.count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": paginator.num_pages
                },
                "filters": {
                    "search": search,
                    "status": status_filter,
                    "order_by": order_by
                }
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

    def _get_user_profile(self, user):
        """获取用户资料信息"""
        try:
            profile = UserProfile.objects.get(user=user)
            return {
                "nickname": profile.nickname,
                "avatar": profile.avatar.url if profile.avatar else None
            }
        except UserProfile.DoesNotExist:
            return {}

    def _get_user_stats(self, user):
        """获取用户统计数据"""
        return {
            "total_comments": Comment.objects.filter(user=user).count(),
            "total_replies": Reply.objects.filter(user=user).count(),
            "animes_created": Anime.objects.filter(created_by=user).count()
        }

@method_decorator(csrf_exempt, name='dispatch')
class UserStatusView(APIView):
    """获取单个用户状态"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        try:
            # 获取目标用户
            target_user = User.objects.get(id=user_id)
            
            # 获取用户当前状态 - 直接使用 is_active
            user_status = "ACTIVE" if target_user.is_active else "BANNED"
            
            # 获取封禁操作历史
            ban_logs = UserBanLog.objects.filter(user=target_user).select_related('operated_by').order_by('-operated_at')
            ban_history = []
            
            for log in ban_logs:
                ban_history.append({
                    "id": log.id,
                    "action": log.action,
                    "action_display": log.get_action_display(),
                    "reason": log.reason,
                    "ban_duration": log.ban_duration,
                    "ban_until": log.ban_until.isoformat() if log.ban_until else None,
                    "operated_by": {
                        "user_id": log.operated_by.id,
                        "username": log.operated_by.username
                    },
                    "operated_at": log.operated_at.isoformat() if log.operated_at else None
                })
            
            # 获取用户统计数据和资料
            user_stats = self._get_user_stats(target_user)
            user_profile = self._get_user_profile(target_user)
            
            response_data = {
                "user_id": target_user.id,
                "username": target_user.username,
                "email": target_user.email,
                "is_active": target_user.is_active,
                "is_staff": target_user.is_staff,
                "date_joined": target_user.date_joined.isoformat() if target_user.date_joined else None,
                "last_login": target_user.last_login.isoformat() if target_user.last_login else None,
                "status": user_status,
                "status_display": "正常" if target_user.is_active else "已封禁",
                "profile": user_profile,
                "ban_history": ban_history,
                "user_stats": user_stats
            }

            return Response({
                "code": 200,
                "message": "success",
                "data": response_data
            })

        except User.DoesNotExist:
            return Response({
                "code": 404,
                "message": "用户不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_user_profile(self, user):
        """获取用户资料信息"""
        try:
            profile = UserProfile.objects.get(user=user)
            return {
                "nickname": profile.nickname,
                "signature": profile.signature,
                "gender": profile.gender,
                "location": profile.location,
                "website": profile.website,
                "avatar": profile.avatar.url if profile.avatar else None
            }
        except UserProfile.DoesNotExist:
            return {}

    def _get_user_stats(self, user):
        """获取用户统计数据"""
        return {
            "total_comments": Comment.objects.filter(user=user).count(),
            "total_replies": Reply.objects.filter(user=user).count(),
            "animes_created": Anime.objects.filter(created_by=user).count(),
            "reports_created": Report.objects.filter(reporter=user).count(),
            "reports_against": Report.objects.filter(
                content_type=ContentType.objects.get_for_model(Comment),
                object_id__in=Comment.objects.filter(user=user).values_list('id', flat=True)
            ).count() + Report.objects.filter(
                content_type=ContentType.objects.get_for_model(Anime),
                object_id__in=Anime.objects.filter(created_by=user).values_list('id', flat=True)
            ).count() + Report.objects.filter(
                content_type=ContentType.objects.get_for_model(Reply),
                object_id__in=Reply.objects.filter(user=user).values_list('id', flat=True)
            ).count()
        }

@method_decorator(csrf_exempt, name='dispatch')
class BanUserView(APIView):
    """封禁用户 - 使用 is_active=False"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, user_id):
        try:
            # 解析请求体
            data = json.loads(request.body)
            reason = data.get('reason')
            ban_duration = data.get('ban_duration', 7)  # 默认7天
            delete_content = data.get('delete_content', False)

            # 参数验证
            if not reason:
                return Response({
                    "code": 400,
                    "message": "封禁理由不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取目标用户
            target_user = User.objects.get(id=user_id)
            
            # 检查是否已经是封禁状态
            if not target_user.is_active:
                return Response({
                    "code": 400,
                    "message": "用户已被封禁",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 计算封禁结束时间（用于记录，实际封禁是永久的直到手动解封）
            ban_until = timezone.now() + timezone.timedelta(days=ban_duration) if ban_duration else None

            # 执行封禁：设置 is_active = False
            target_user.is_active = False
            target_user.save()

            # 记录封禁日志
            ban_log = UserBanLog.objects.create(
                user=target_user,
                action='BAN',
                reason=reason,
                ban_duration=ban_duration,
                ban_until=ban_until,
                operated_by=request.user
            )

            # 如果需要删除用户内容
            content_deleted = False
            if delete_content:
                content_deleted = self._delete_user_content(target_user)

            # 记录管理员操作日志
            self._log_admin_action(
                admin=request.user,
                action_type='BAN_USER',
                target_user=target_user,
                description=f"封禁用户 {target_user.username}，理由：{reason}" + (f"，时长：{ban_duration}天" if ban_duration else "")
            )

            response_data = {
                "user_id": target_user.id,
                "username": target_user.username,
                "is_active": False,
                "reason": reason,
                "ban_duration": ban_duration,
                "banned_until": ban_until.isoformat() if ban_until else None,
                "banned_by": {
                    "user_id": request.user.id,
                    "username": request.user.username
                },
                "delete_content": delete_content,
                "content_deleted": content_deleted,
                "ban_log_id": ban_log.id
            }

            return Response({
                "code": 200,
                "message": "用户封禁成功",
                "data": response_data
            })

        except User.DoesNotExist:
            return Response({
                "code": 404,
                "message": "用户不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
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

    def _delete_user_content(self, user):
        """删除用户内容（软删除）"""
        try:
            deleted_count = 0
            
            # 标记用户的评论为已删除
            comments_updated = Comment.objects.filter(user=user).update(is_banned=True)
            deleted_count += comments_updated
            
            # 标记用户的回复为已删除
            replies_updated = Reply.objects.filter(user=user).update(is_banned=True)
            deleted_count += replies_updated
            
            # 标记用户创建的番剧条目为已删除
            animes_updated = Anime.objects.filter(created_by=user).update(is_banned=True)
            deleted_count += animes_updated
            
            print(f"已软删除用户 {user.username} 的 {deleted_count} 条内容")
            return deleted_count > 0
        except Exception as e:
            print(f"删除用户内容失败: {e}")
            return False

    def _log_admin_action(self, admin, action_type, target_user, description):
        """记录管理员操作日志"""
        try:
            AdminLog.objects.create(
                admin=admin,
                action_type=action_type,
                target_user=target_user,
                description=description,
                ip_address=self._get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"记录管理员日志失败: {e}")

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@method_decorator(csrf_exempt, name='dispatch')
class UnbanUserView(APIView):
    """解封用户 - 使用 is_active=True"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, user_id):
        try:
            # 解析请求体
            data = json.loads(request.body)
            reason = data.get('reason', '')
            restore_content = data.get('restore_content', False)

            # 获取目标用户
            target_user = User.objects.get(id=user_id)
            
            # 检查用户是否已被封禁
            if target_user.is_active:
                return Response({
                    "code": 400,
                    "message": "用户当前未被封禁",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 执行解封：设置 is_active = True
            target_user.is_active = True
            target_user.save()

            # 记录解封日志
            unban_log = UserBanLog.objects.create(
                user=target_user,
                action='UNBAN',
                reason=reason,
                operated_by=request.user
            )

            # 如果需要恢复用户内容
            content_restored = False
            if restore_content:
                content_restored = self._restore_user_content(target_user)

            # 记录管理员操作日志
            self._log_admin_action(
                admin=request.user,
                action_type='UNBAN_USER',
                target_user=target_user,
                description=f"解封用户 {target_user.username}，理由：{reason}"
            )

            response_data = {
                "user_id": target_user.id,
                "username": target_user.username,
                "is_active": True,
                "unbanned_at": timezone.now().isoformat(),
                "unbanned_by": {
                    "user_id": request.user.id,
                    "username": request.user.username
                },
                "reason": reason,
                "restore_content": restore_content,
                "content_restored": content_restored,
                "unban_log_id": unban_log.id
            }

            return Response({
                "code": 200,
                "message": "用户解封成功",
                "data": response_data
            })

        except User.DoesNotExist:
            return Response({
                "code": 404,
                "message": "用户不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
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

    def _restore_user_content(self, user):
        """恢复用户内容"""
        try:
            restored_count = 0
            
            # 恢复用户的评论
            comments_restored = Comment.objects.filter(user=user, is_banned=True).update(is_banned=False)
            restored_count += comments_restored
            
            # 恢复用户的回复
            replies_restored = Reply.objects.filter(user=user, is_banned=True).update(is_banned=False)
            restored_count += replies_restored
            
            # 恢复用户创建的番剧条目
            animes_restored = Anime.objects.filter(created_by=user, is_banned=True).update(is_banned=False)
            restored_count += animes_restored
            
            print(f"已恢复用户 {user.username} 的 {restored_count} 条内容")
            return restored_count > 0
        except Exception as e:
            print(f"恢复用户内容失败: {e}")
            return False

    def _log_admin_action(self, admin, action_type, target_user, description):
        """记录管理员操作日志"""
        try:
            AdminLog.objects.create(
                admin=admin,
                action_type=action_type,
                target_user=target_user,
                description=description,
                ip_address=self._get_client_ip(self.request),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"记录管理员日志失败: {e}")

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip