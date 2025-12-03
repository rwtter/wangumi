from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from ..models import Anime, Person,Character,UserProfile

def _do_search(query, model, sort, is_admin_filter=None):
    """
    通用搜索函数
    :param query: 搜索关键词
    :param model: 搜索的模型
    :param sort: 排序方式
    :param is_admin_filter: None(不过滤), True(仅Anime), False(仅Item)
    """
    # 尝试多种搜索策略以获得最佳匹配结果
    search_strategies = [
        SearchQuery(query, search_type='websearch'),  # 网络搜索风格，支持AND/OR
        SearchQuery(query, search_type='plain'),     # 纯文本搜索
        SearchQuery(query, search_type='phrase')     # 短语精确匹配
    ]

    # 合并多个搜索策略的结果，去重并按最高相关性排序
    all_results = []
    seen_ids = set()

    for search_query in search_strategies:
        qs = model.objects.annotate(
            rank=SearchRank(F("search_vector"), search_query)
        ).filter(rank__gt=0.001)  # 进一步降低阈值以提高召回率

        for obj in qs:
            # 处理不同模型的ID字段
            if hasattr(obj, 'id'):
                obj_id = obj.id
            elif hasattr(obj, 'pers_id'):
                obj_id = obj.pers_id
            else:
                continue

            if obj_id not in seen_ids:
                seen_ids.add(obj_id)
                obj._current_rank = obj.rank  # 临时存储rank值
                all_results.append(obj)

    # 如果需要按 is_admin 过滤，需要重新查询
    if is_admin_filter is not None and hasattr(model, 'is_admin'):
        all_results = [obj for obj in all_results if getattr(obj, 'is_admin', None) == is_admin_filter]

    # 根据排序方式对结果进行排序
    if sort == "relevance":
        all_results.sort(key=lambda x: x._current_rank, reverse=True)
    elif sort == "popularity":
        all_results.sort(key=lambda x: getattr(x, 'popularity', 0), reverse=True)
    elif sort == "time":
        all_results.sort(key=lambda x: getattr(x, 'created_at', ''), reverse=True)

    result = []
    for obj in all_results:
        # 处理不同模型的ID字段
        if hasattr(obj, 'id'):
            obj_id = obj.id
        elif hasattr(obj, 'pers_id'):
            obj_id = obj.pers_id
        else:
            continue  # 跳过没有ID的对象

        # 处理名称字段，按模型类型优先级获取
        name = None
        if hasattr(obj, 'name'):
            name = obj.name
        elif hasattr(obj, 'pers_name'):
            name = obj.pers_name
        elif hasattr(obj, 'nickname'):  # UserProfile优先使用nickname
            name = obj.nickname
        elif hasattr(obj, 'user') and hasattr(obj.user, 'username'):
            name = obj.user.username

        result.append({
            "id": obj_id,
            "title": getattr(obj, "title", None),
            "name": name,
            "cover_url": getattr(obj, "cover_url", None),
            "image_url": getattr(obj, "image", None),  # 若为character模型，则使用 image 字段
            "pers_image_url": getattr(obj, "pers_img", None),  # 若为Person模型，则使用 pers_img 字段
            "avatar_url": str(getattr(obj, "avatar", "")) if getattr(obj, "avatar", None) else None,  # 若为Userprofile模型，则使用avatar字段，并转换为字符串
            "related_score": obj._current_rank,  # 使用临时存储的rank值
            "is_admin": getattr(obj, "is_admin", None),  # 添加 is_admin 字段用于区分
        })

    return result


def search_single_type(query, type_name, sort):
    # 多模型的方式（一个 type 可以对应多个 model）
    model_map = {
        "anime": [(Anime, True)],
        "item": [(Anime, False)],
        "person": [(Person, None), (Character, None)],#person 同时对应Person 和 Character 模型
        "user":[(UserProfile,None)],
    }

    model_list = model_map[type_name]

    results = []
    for model, admin_filter in model_list:
        res = _do_search(query, model, sort, admin_filter)
        results.extend(res)

    return results


def search_all_types(query, sort):
    return {
        "anime": _do_search(query, Anime, sort, is_admin_filter=True),
        "item": _do_search(query, Anime, sort, is_admin_filter=False),
        "person": (
            _do_search(query, Person, sort, None)
            + _do_search(query, Character, sort, None)
        ),#person 类型包含 Person 和 Character 两个模型的结果
        "user":_do_search(query, UserProfile, sort, None)
    }
