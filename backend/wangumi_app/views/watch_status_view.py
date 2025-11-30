import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from wangumi_app.models import WatchStatus, Anime
from wangumi_app.views.user_activities_view import create_activity


@method_decorator(csrf_exempt, name='dispatch')
class WatchStatusView(APIView):
    """追番状态接口 - 设置/更新和获取追番状态"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """设置或更新追番状态"""
        try:
            data = json.loads(request.body)
            anime_id = data.get('anime_id')
            status_value = data.get('status')  # 重命名避免与status模块冲突

            # 参数验证
            if not anime_id:
                return Response({
                    "code": 400,
                    "message": "anime_id不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            if not status_value:
                return Response({
                    "code": 400,
                    "message": "status不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证status值
            valid_statuses = [choice[0] for choice in WatchStatus.STATUS_CHOICES]
            if status_value not in valid_statuses:
                return Response({
                    "code": 400,
                    "message": f"status值必须是以下之一: {', '.join(valid_statuses)}",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证番剧是否存在
            try:
                anime = Anime.objects.get(id=anime_id)
            except Anime.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "番剧不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 创建或更新追番记录
            watch_status, created = WatchStatus.objects.update_or_create(
                user=request.user,
                anime=anime,
                defaults={'status': status_value}
            )
            # 更新番剧的热度
            if created:
                anime.popularity += 1
                anime.save()

            if status_value=="WATCHING" and created:
                create_activity(request.user,watch_status, "新增追番")

            action = "创建" if created else "更新"
            response_data = {
                "id": watch_status.id,
                "user_id": request.user.id,
                "anime_id": anime.id,
                "anime_title": anime.title,
                "status": watch_status.status,
                "status_display": watch_status.get_status_display(),
                "updated_at": watch_status.updated_at.isoformat()
            }

            return Response({
                "code": 200,
                "message": f"追番状态{action}成功",
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

    def get(self, request):
        """获取追番状态 - 支持JSON请求体"""
        try:
            # 尝试从请求体中解析JSON
            anime_id = None

            # 检查是否有请求体内容
            if request.body:
                try:
                    # 解析JSON请求体
                    body_data = json.loads(request.body)
                    anime_id = body_data.get('anime_id')
                except json.JSONDecodeError:
                    # 如果JSON解析失败，回退到URL参数
                    anime_id = request.GET.get('anime_id')
            else:
                # 如果没有请求体，使用URL参数
                anime_id = request.GET.get('anime_id')
            
            #print(f"Debug: 获取到的anime_id = {anime_id}")
            
            if anime_id:
                # 获取特定番剧的追番状态
                try:
                    anime_id = int(anime_id)
                except ValueError:
                    return Response({
                        "code": 400,
                        "message": "anime_id必须是整数",
                        "data": None
                    }, status=status.HTTP_400_BAD_REQUEST)

                # 验证番剧是否存在
                try:
                    anime = Anime.objects.get(id=anime_id)
                except Anime.DoesNotExist:
                    return Response({
                        "code": 404,
                        "message": "番剧不存在",
                        "data": None
                    }, status=status.HTTP_404_NOT_FOUND)

                # 查询追番状态
                try:
                    watch_status = WatchStatus.objects.get(
                        user=request.user,
                        anime=anime
                    )
                    
                    response_data = {
                        "anime_id": anime.id,
                        "anime_title": anime.title,
                        "status": watch_status.status,
                        "status_display": watch_status.get_status_display(),
                        "updated_at": watch_status.updated_at.isoformat()
                    }

                    return Response({
                        "code": 200,
                        "data": response_data
                    })
                    
                except WatchStatus.DoesNotExist:
                    return Response({
                        "code": 404,
                        "message": "未找到追番记录",
                        "data": {
                            "anime_id": anime_id,
                            "status": None
                        }
                    }, status=status.HTTP_404_NOT_FOUND)

            else:
                # 获取所有追番状态
                watch_statuses = WatchStatus.objects.filter(
                    user=request.user
                ).select_related('anime').order_by('-updated_at')

                watch_list = []
                for watch_status in watch_statuses:
                    watch_list.append({
                        "anime_id": watch_status.anime.id,
                        "anime_title": watch_status.anime.title,
                        "status": watch_status.status,
                        "status_display": watch_status.get_status_display(),
                        "updated_at": watch_status.updated_at.isoformat()
                    })

                return Response({
                    "code": 200,
                    "data": {
                        "watch_list": watch_list,
                        "total": len(watch_list)
                    }
                })

        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        """删除追番状态 - 支持JSON请求体"""
        try:
            # 尝试从请求体中解析JSON
            anime_id = None
            
            # 检查是否有请求体内容
            if request.body:
                try:
                    # 解析JSON请求体
                    body_data = json.loads(request.body)
                    anime_id = body_data.get('anime_id')
                    #print(f"Debug: 从JSON请求体获取的anime_id = {anime_id}")
                except json.JSONDecodeError:
                    # 如果JSON解析失败，回退到URL参数
                    anime_id = request.GET.get('anime_id')
                    #print(f"Debug: JSON解析失败，使用URL参数 anime_id = {anime_id}")
            else:
                # 如果没有请求体，使用URL参数
                anime_id = request.GET.get('anime_id')
                #print(f"Debug: 无请求体，使用URL参数 anime_id = {anime_id}")
            
            if not anime_id:
                return Response({
                    "code": 400,
                    "message": "anime_id参数不能为空",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                anime_id = int(anime_id)
            except ValueError:
                return Response({
                    "code": 400,
                    "message": "anime_id必须是整数",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

            # 验证番剧是否存在
            try:
                anime = Anime.objects.get(id=anime_id)
            except Anime.DoesNotExist:
                return Response({
                    "code": 404,
                    "message": "番剧不存在",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)

            # 查找并删除追番记录
            deleted_count, _ = WatchStatus.objects.filter(
                user=request.user,
                anime=anime
            ).delete()

            if deleted_count == 0:
                return Response({
                    "code": 404,
                    "message": "未找到追番记录",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
            
            # 更新番剧的热度
            anime.popularity = max(0, anime.popularity - 1)
            anime.save()
            
            return Response({
                "code": 200,
                "message": "追番状态已删除",
                "data": {
                    "anime_id": anime_id,
                    "anime_title": anime.title
                }
            })

        except Exception as e:
            return Response({
                "code": 500,
                "message": f"服务器内部错误: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)