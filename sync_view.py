from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from wangumi_app.models import SyncLog
from wangumi_app.services.weekly_sync_service import sync_weekly_collections


class WeeklySyncView(APIView):
    """手动触发周合集同步，返回本次日志信息"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        success, stats = sync_weekly_collections()
        log = SyncLog.objects.get(id=stats["log_id"]) if stats else None

        payload = {
            "log_id": log.id if log else None,
            "status": log.status if log else None,
            "message": log.message if log else "",
            "created": log.created_count if log else 0,
            "updated": log.updated_count if log else 0,
            "finished_at": log.finished_at.isoformat() if log and log.finished_at else None,
        }

        return Response(
            {
                "code": 0 if success else 500,
                "message": log.message if log else "同步失败",
                "data": payload,
            },
            status=status.HTTP_200_OK if success else status.HTTP_500_INTERNAL_SERVER_ERROR,
        )