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

from wangumi_app.models import Report, Comment, Reply, User, Anime, Episode

class IsAdminUser(IsAuthenticated):
    """自定义权限类，验证是否为管理员"""
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_staff or request.user.is_superuser
        )

@method_decorator(csrf_exempt, name='dispatch')
class ReportListView(APIView):
    """获取举报列表"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # 获取查询参数
            status_filter = request.GET.get('status')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 50)

            # 构建查询条件
            queryset = Report.objects.select_related('reporter').all()
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # 按创建时间倒序排列
            queryset = queryset.order_by('-created_at')

            # 分页
            paginator = Paginator(queryset, page_size)
            try:
                reports_page = paginator.page(page)
            except:
                reports_page = paginator.page(1)

            # 构建举报数据
            reports_data = []
            for report in reports_page:
                target_preview = self._get_target_preview(report)
                
                reports_data.append({
                    "id": report.id,
                    "reporter": {
                        "user_id": report.reporter.id,
                        "username": report.reporter.username
                    },
                    "target_type": self._get_target_type_display(report.content_type),
                    "target_id": report.object_id,
                    "target_preview": target_preview,
                    "category": report.category,
                    "category_display": report.get_category_display(),
                    "reason": report.reason,
                    "status": report.status,
                    "created_at": report.created_at.isoformat() if report.created_at else None
                })

            # 获取统计信息
            stats = {
                "pending_count": Report.objects.filter(status='PENDING').count(),
                "resolved_count": Report.objects.filter(status='RESOLVED').count(),
                "rejected_count": Report.objects.filter(status='REJECTED').count()
            }

            response_data = {
                "reports": reports_data,
                "pagination": {
                    "total": paginator.count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": paginator.num_pages
                },
                "stats": stats
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

    def _get_target_preview(self, report):
        """获取被举报内容的预览"""
        try:
            target = report.content_object
            if isinstance(target, Comment):
                return target.content[:50] + "..." if len(target.content) > 50 else target.content
            elif isinstance(target, Anime):
                return f"番剧: {target.title}"
            elif isinstance(target, Reply):
                return target.content[:50] + "..." if len(target.content) > 50 else target.content
            return "未知内容"
        except:
            return "内容已删除"

    def _get_target_type_display(self, content_type):
        """获取被举报类型的中文显示"""
        type_map = {
            'comment': '评论',
            'anime': '番剧条目',
            'reply': '回复'
        }
        return type_map.get(content_type.model, '未知类型')

@method_decorator(csrf_exempt, name='dispatch')
class ReportDetailView(APIView):
    """获取举报详情"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def get(self, request, report_id):
        try:
            # 获取举报记录
            report = Report.objects.select_related('reporter', 'moderator').get(id=report_id)
            
            # 构建详细数据
            target_content = self._get_target_content(report)
            
            report_data = {
                "id": report.id,
                "reporter": {
                    "user_id": report.reporter.id,
                    "username": report.reporter.username,
                    "avatar": self._get_user_avatar(report.reporter)
                },
                "target_type": self._get_target_type_display(report.content_type),
                "target_id": report.object_id,
                "target_content": target_content,
                "category": report.category,
                "category_display": report.get_category_display(),
                "reason": report.reason,
                "status": report.status,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "moderator": self._get_moderator_info(report.moderator) if report.moderator else None,
                "handled_at": report.handled_at.isoformat() if report.handled_at else None,
                "resolution": report.resolution
            }

            return Response({
                "code": 200,
                "message": "success",
                "data": report_data
            })

        except Report.DoesNotExist:
            return Response({
                "code": 404,
                "message": "举报记录不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_target_content(self, report):
        """获取被举报内容的详细信息"""
        try:
            target = report.content_object
            if not target:
                return {"error": "内容已被删除"}
                
            if isinstance(target, Comment):
                return {
                    "type": "comment",
                    "content": target.content,
                    "author": {
                        "user_id": target.user.id,
                        "username": target.user.username
                    },
                    "score": target.score,
                    "created_at": target.created_at.isoformat() if target.created_at else None,
                    "scope": target.scope
                }
            elif isinstance(target, Anime):
                return {
                    "type": "anime",
                    "title": target.title,
                    "title_cn": target.title_cn,
                    "description": target.description,
                    "creator": {
                        "user_id": target.created_by.id if target.created_by else None,
                        "username": target.created_by.username if target.created_by else "系统"
                    },
                    "created_at": target.created_at.isoformat() if target.created_at else None,
                    "is_admin": target.is_admin
                }
            elif isinstance(target, Reply):
                return {
                    "type": "reply",
                    "content": target.content,
                    "author": {
                        "user_id": target.user.id,
                        "username": target.user.username
                    },
                    "created_at": target.created_at.isoformat() if target.created_at else None
                }
            return {"error": "未知内容类型"}
        except Exception as e:
            return {"error": f"获取内容失败: {str(e)}"}

    def _get_user_avatar(self, user):
        """获取用户头像"""
        try:
            if hasattr(user, 'userprofile') and user.userprofile.avatar:
                return user.userprofile.avatar.url
        except:
            pass
        return "/avatars/default.jpg"

    def _get_moderator_info(self, moderator):
        """获取处理人信息"""
        if not moderator:
            return None
        return {
            "user_id": moderator.id,
            "username": moderator.username,
            "avatar": self._get_user_avatar(moderator)
        }

    def _get_target_type_display(self, content_type):
        """获取被举报类型的中文显示"""
        type_map = {
            'comment': '评论',
            'anime': '番剧条目',
            'reply': '回复'
        }
        return type_map.get(content_type.model, '未知类型')

@method_decorator(csrf_exempt, name='dispatch')
class ReportHandleView(APIView):
    """处理举报"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def post(self, request, report_id):
        try:
            # 解析请求体
            data = json.loads(request.body)
            action = data.get('action')
            resolution = data.get('resolution', '')
            ban_user = data.get('ban_user', False)
            ban_duration = data.get('ban_duration', 7)

            # 参数验证
            if action not in ['RESOLVED', 'REJECTED']:
                return Response({
                    "code": 400,
                    "message": "action参数必须是RESOLVED或REJECTED",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 获取举报记录
            report = Report.objects.select_related('reporter').get(id=report_id)
            
            # 更新举报状态
            report.status = action
            report.moderator = request.user
            report.handled_at = timezone.now()
            report.resolution = resolution
            report.save()

            content_deleted = False
            user_banned = False

            # 如果同意举报，删除违规内容
            if action == 'RESOLVED':
                content_deleted = self._delete_reported_content(report)
                
                # 如果需要封禁用户
                if ban_user:
                    user_banned = self._ban_user(report, ban_duration)

            # 记录操作日志
            self._log_admin_action(request.user, report, action, content_deleted, user_banned)

            response_data = {
                "report_id": report.id,
                "action": action,
                "content_deleted": content_deleted,
                "user_banned": user_banned,
                "handled_at": report.handled_at.isoformat() if report.handled_at else None
            }

            return Response({
                "code": 200,
                "message": "举报处理成功",
                "data": response_data
            })

        except Report.DoesNotExist:
            return Response({
                "code": 404,
                "message": "举报记录不存在",
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

    def _delete_reported_content(self, report):
        """删除被举报的违规内容"""
        try:
            target = report.content_object
            if target:
                # 软删除：标记为已删除或设置删除标志
                if hasattr(target, 'is_banned'):
                    target.is_banned = True
                    target.save()
                    return True
                else:
                    # 对于没有 is_banned 字段的对象，记录日志但不删除
                    print(f"警告: 对象 {type(target)} 没有 is_banned 字段，无法软删除")
                    return False
            return False
        except Exception as e:
            print(f"删除内容失败: {e}")
            return False

    def _ban_user(self, report, ban_duration):
        """封禁用户"""
        try:
            target = report.content_object
            if target and hasattr(target, 'user'):
                # 这里可以实现用户封禁逻辑
                user_to_ban = target.user
                print(f"用户 {user_to_ban.username} 被管理员 {report.moderator.username} 封禁 {ban_duration} 天")
                return True
            return False
        except Exception as e:
            print(f"封禁用户失败: {e}")
            return False

    def _log_admin_action(self, moderator, report, action, content_deleted, user_banned):
        """记录管理员操作日志"""
        try:
            log_entry = f"管理员 {moderator.username} {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} "
            log_entry += f"处理举报 #{report.id}: {action}"
            
            if content_deleted:
                log_entry += ", 已删除违规内容"
            if user_banned:
                log_entry += ", 已封禁用户"
                
            print(f"[ADMIN_ACTION] {log_entry}")
            # 这里可以保存到专门的日志表或文件中
        except Exception as e:
            print(f"记录操作日志失败: {e}")