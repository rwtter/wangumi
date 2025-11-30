from functools import reduce

from django.core.paginator import Paginator
from django.db.models import Max, Q
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken

from wangumi_app.models import Anime, AnimeStaff, CharacterAppearance, CharacterVoice, Episode, Comment
from wangumi_app.views.user_activities_view import create_activity

STATUS_DISPLAY = {
    "FINISHED": "已完结",
    "RELEASING": "连载中",
    "NOT_YET_RELEASED": "未开播",
    "CANCELLED": "已取消",
    "HIATUS": "暂停连载",
}


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


def _build_anime_list_response(request, base_queryset):
    raw_sort = (request.GET.get("sort") or "").strip()
    sort_map = {
        "热度": "-popularity",
        "hot": "-popularity",
        "popularity": "-popularity",
        "时间": "-updated_at",
        "time": "-updated_at",
        "updated_at": "-updated_at",
        "评分": "-rating",
        "rating": "-rating",
        "score": "-rating",
    }
    if raw_sort:
        order_by = sort_map.get(raw_sort) or sort_map.get(raw_sort.lower())
        if order_by is None:
            return _build_error_response("sort 参数仅支持 热度/时间/评分")
    else:
        order_by = "-popularity"

    try:
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 20))
    except ValueError:
        return _build_error_response("page 和 limit 需要是正整数")

    if page <= 0 or limit <= 0:
        return _build_error_response("page 和 limit 需要是正整数")

    limit = min(limit, 100)

    raw_category = (request.GET.get("category") or "").strip()
    categories = [item.strip() for item in raw_category.split(",") if item.strip()] if raw_category else []

    queryset = base_queryset
    if categories:
        q_objects = [
            Q(genres__contains=[category_name])
            for category_name in categories
        ]
        combined = reduce(lambda acc, q: acc | q, q_objects)
        queryset = queryset.filter(combined)

    queryset = queryset.order_by(order_by)

    paginator = Paginator(queryset, limit)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)

    results = []
    for anime in page_obj.object_list:
        results.append(
            {
                "id": anime.id,
                "title": anime.title,
                "cover": _resolve_cover_url(anime),
                "rating": anime.rating,
                "popularity": anime.popularity,
                "summary": anime.description,
                "time": anime.updated_at.isoformat() if anime.updated_at else None,
                "category": anime.genres or [],
                "isAdmin": anime.is_admin,
            }
        )

    response_payload = {
        "code": 0,
        "message": "success",
        "data": {
            "list": results,
            "pagination": {
                "page": page_obj.number if paginator.count else page,
                "limit": limit,
                "total": paginator.count,
                "pages": paginator.num_pages,
            },
            "sort": raw_sort or "热度",
            "category_filter": categories,
        },
    }
    return JsonResponse(response_payload, json_dumps_params={'ensure_ascii': False})


def authenticate_user(request):
    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False):
        return user
    authenticator = JWTAuthentication()
    try:
        auth_result = authenticator.authenticate(request)
    except (AuthenticationFailed, InvalidToken):
        return None
    if not auth_result:
        return None
    return auth_result[0]


class AnimeListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # 允许未登录访问 GET 列表
        if getattr(self.request, 'method', 'GET') == 'GET':
            return []
        return super().get_permissions()

    def get(self, request):
        """
            sort: 排序方式 (热度/时间/评分, 默认热度)
            category: 用逗号分隔的类别列表（可选）
            page: 页码 (默认 1)
            limit: 每页数量 (默认 20)
        返回值：
        JsonResponse {code, message, data}.
        """
        base_queryset = Anime.objects.all()
        return _build_anime_list_response(request, base_queryset)

    def post(self, request):
        """
        创建番剧（需登录）
        支持 multipart/form-data 上传封面。
        必填：title
        可选：title_cn、description、genres、release_date、status、total_episodes
        文件：cover
        """
        data = request.data if hasattr(request, 'data') else request.POST

        title = (data.get('title') or '').strip()
        if not title:
            return _build_error_response("必填项未填写完整：标题不能为空", status=400)

        title_cn = (data.get('title_cn') or data.get('titleCN') or '').strip() or title
        description = (data.get('description') or data.get('summary') or '').strip()
        status_value = (data.get('status') or '').strip()

        raw_genres = data.get('genres')
        genres = []
        if isinstance(raw_genres, list):
            genres = [str(x).strip() for x in raw_genres if str(x).strip()]
        elif isinstance(raw_genres, str):
            genres = [x.strip() for x in raw_genres.split(',') if x.strip()]

        # 可选：release_date、total_episodes
        release_date = data.get('release_date') or data.get('releaseDate')
        total_episodes = data.get('total_episodes') or data.get('episodes')
        try:
            total_episodes = int(total_episodes) if total_episodes not in (None, "",) else 0
        except Exception:
            return _build_error_response("total_episodes 必须是整数", status=400)

        cover = None
        files = getattr(request, 'FILES', None)
        if files:
            cover = files.get('cover') or files.get('cover_image') or files.get('file')

        cover_url_value = (data.get('cover_url') or data.get('coverUrl') or '').strip()

        anime = Anime(
            title=title,
            title_cn=title_cn,
            description=description,
            genres=genres,
            status=status_value,
            total_episodes=total_episodes,
        )
        if release_date:
            try:
                # 接受 YYYY-MM-DD 格式
                from datetime import date
                anime.release_date = date.fromisoformat(str(release_date))
            except Exception:
                return _build_error_response("release_date 格式应为 YYYY-MM-DD", status=400)
        if cover:
            anime.cover_image = cover
            anime.cover_url = ""
        elif cover_url_value:
            anime.cover_url = cover_url_value
        # 保存创建者（新增字段 created_by，可能为可空）
        if hasattr(anime, 'created_by'):
            anime.created_by = request.user
        if hasattr(anime, 'is_admin'):
            anime.is_admin = bool(getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False))
        anime.save()

        detail_url = f"/api/anime/{anime.id}"
        if not anime.is_admin:
            create_activity(request.user,anime, "新建了条目")
        return JsonResponse({
            "code": 0,
            "message": "条目创建成功",
            "data": {
                "id": anime.id,
                "detailUrl": detail_url,
            }
        }, status=201, json_dumps_params={'ensure_ascii': False})


def anime_delete(request, anime_id: int):
    anime = Anime.objects.filter(pk=anime_id).first()
    if not anime:
        return JsonResponse({"code": 404, "message": "番剧不存在", "data": None}, status=404)
    user = authenticate_user(request)
    if user is None:
        return _build_error_response("需要登录才能删除条目", status=401)
    is_admin_user = bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    if anime.is_admin and not is_admin_user:
        return _build_error_response("仅管理员可以删除官方条目", status=403)
    if not is_admin_user and anime.created_by_id != user.id:
        return _build_error_response("无权限删除该条目", status=403)
    anime.delete()
    return JsonResponse(
        {"code": 0, "message": "条目删除成功", "data": {"id": anime_id}},
        status=200,
        json_dumps_params={'ensure_ascii': False}
    )


class UserEntryListView(APIView):

    def get(self, request):
        queryset = Anime.objects.filter(is_admin=False)
        return _build_anime_list_response(request, queryset)


def anime_detail(request, anime_id: int):
    if request.method == "DELETE":
        return anime_delete(request, anime_id)
    if request.method != "GET":
        return JsonResponse({"code": 405, "message": "Method Not Allowed", "data": None}, status=405)
    anime = Anime.objects.filter(pk=anime_id).first()
    if not anime:
        return JsonResponse({"code": 404, "message": "番剧不存在", "data": None}, status=404)

    character_appearances = (
        CharacterAppearance.objects.filter(anime=anime)
        .select_related("character")
        .order_by("order", "id")
    )
    character_ids = [appearance.character_id for appearance in character_appearances if appearance.character_id]
    voices = (
        CharacterVoice.objects.filter(character_id__in=character_ids)
        .select_related("person")
    )
    voices_by_character = {}
    for voice in voices:
        voices_by_character.setdefault(voice.character_id, []).append(voice.person.pers_name)

    characters_payload = []
    for appearance in character_appearances:
        character = appearance.character
        if character is None:
            continue
        characters_payload.append(
            {
                "name": character.name,
                "avatar": character.image or "",
                "voiceActors": voices_by_character.get(character.id, []),
            }
        )

    staff_members = (
        AnimeStaff.objects.filter(anime=anime)
        .select_related("person", "role", "character")
        .order_by("order", "id")
    )
    staff_payload = []
    for member in staff_members:
        staff_entry = {
            "role": member.role.name if member.role else "",
            "name": member.person.pers_name if member.person else "",
        }
        if member.character:
            staff_entry["character"] = member.character.name
        staff_payload.append(staff_entry)

    max_episode = (
        Episode.objects.filter(anime=anime).aggregate(max_ep=Max("episode_number")).get("max_ep")
    )
    if max_episode:
        update_progress = f"已更新至第{max_episode}集"
    elif anime.total_episodes:
        update_progress = f"共{anime.total_episodes}集"
    else:
        update_progress = "暂无更新信息"

    status_display = STATUS_DISPLAY.get((anime.status or "").upper(), anime.status or "未知")

    comment_lists= (
        Comment.objects.filter(object_id=anime.id)
            .select_related('user')
            .order_by('-created_at') 
        )
    comment_payload = []
    for comment in comment_lists:
        comment_payload.append({
            "user": comment.user.username if comment.user else "匿名",
            "content": comment.content,
            "createdAt": comment.created_at.isoformat() if comment.created_at else None,
        })

    data = {
        "basic": {
            "id": anime.id,
            "title": anime.title,
            "titleJapanese": anime.title_cn,
            "cover": _resolve_cover_url(anime),
            "rating": anime.rating,
            "summary": anime.description,
        },
        "meta": {
            "category": anime.genres or [],
            "status": status_display,
            "episodes": anime.total_episodes,
            "releaseDate": anime.release_date.isoformat() if anime.release_date else None,
            "updateProgress": update_progress,
            "createdBy": getattr(getattr(anime, 'created_by', None), 'username', None),
            "createdAt": anime.created_at.isoformat() if anime.created_at else None,
            "isAdmin": anime.is_admin,
        },
        "relations": {
            "characters": characters_payload,
            "staff": staff_payload,
        },
        "comments":{
            "list": comment_payload,
        }
    }

    return JsonResponse({"code": 0, "message": "success", "data": data}, json_dumps_params={'ensure_ascii': False})
