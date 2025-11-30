import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from wangumi_app.models import Comment, Report

@method_decorator(csrf_exempt, name='dispatch')
class ReportView(APIView):
    """举报功能接口 - 提交对评论的举报"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        """提交举报"""
        try:
            # 解析请求体
            data = json.loads(request.body)
            category = data.get('category')
            reason = data.get('reason', '')  # 可选参数，默认为空字符串

            # 参数验证 - category必填
            if not category:
                return Response({
                    "code": 400,
                    "message": "举报分类不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证举报分类有效性
            valid_categories = [choice[0] for choice in Report.REPORT_CATEGORIES]
            if category not in valid_categories:
                return Response({
                    "code": 400,
                    "message": f"举报分类必须是以下之一: {', '.join(valid_categories)}",
                    "data": {
                        "valid_categories": [
                            {"value": cat[0], "label": cat[1]} for cat in Report.REPORT_CATEGORIES
                        ]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证补充说明长度
            if reason and len(reason) > 500:
                return Response({
                    "code": 400,
                    "message": "补充说明不能超过500字符",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证评论是否存在
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "评论不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 检查是否已经举报过该评论（防止重复举报）
            content_type = ContentType.objects.get_for_model(Comment)
            existing_report = Report.objects.filter(
                reporter=request.user,
                content_type=content_type,
                object_id=comment.id
            ).first()

            if existing_report:
                return Response({
                    "code": 400,
                    "message": "您已经举报过该内容",
                    "data": {
                        "existing_report_id": existing_report.id,
                        "previous_category": existing_report.category,
                        "previous_reason": existing_report.reason,
                        "submitted_at": existing_report.created_at.isoformat() if existing_report.created_at else None
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # 创建举报记录
            report = Report.objects.create(
                reporter=request.user,
                content_type=content_type,
                object_id=comment.id,
                category=category,
                reason=reason,
                status='PENDING'
            )

            # 更新评论状态为待审核（如果模型有该字段）
            if hasattr(comment, 'status'):
                comment.status = 'PENDING_REVIEW'
                comment.save(update_fields=['status'])

            # 准备响应数据
            response_data = {
                "report_id": report.id,
                "comment_id": comment.id,
                "category": report.category,
                "category_display": report.get_category_display(),
                "reason": report.reason,
                "status": report.status,
                "status_display": report.get_status_display(),
                "created_at": report.created_at.isoformat() if report.created_at else None
            }

            return Response({
                "code": 201,
                "message": "举报提交成功",
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

    def get(self, request, comment_id):
        """获取当前用户对该评论的举报状态"""
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

            # 查询用户是否已经举报过该评论
            content_type = ContentType.objects.get_for_model(Comment)
            existing_report = Report.objects.filter(
                reporter=request.user,
                content_type=content_type,
                object_id=comment.id
            ).first()

            if existing_report:
                # 用户已经举报过
                response_data = {
                    "has_reported": True,
                    "report_id": existing_report.id,
                    "category": existing_report.category,
                    "category_display": existing_report.get_category_display(),
                    "reason": existing_report.reason,
                    "status": existing_report.status,
                    "status_display": existing_report.get_status_display(),
                    "created_at": existing_report.created_at.isoformat() if existing_report.created_at else None,
                    "comment_id": comment.id
                }
            else:
                # 用户没有举报过
                response_data = {
                    "has_reported": False,
                    "report_id": None,
                    "category": None,
                    "category_display": None,
                    "reason": None,
                    "status": None,
                    "status_display": None,
                    "created_at": None,
                    "comment_id": comment.id
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