from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.paginator import Paginator
from wangumi_app.services.search_service import search_all_types, search_single_type

class SearchView(APIView):
    def get(self, request):
        query = request.GET.get("query", "").strip()
        search_type = request.GET.get("type")
        page = int(request.GET.get("page", 1))
        limit = int(request.GET.get("limit", 20))
        sort = request.GET.get("sort", "relevance")

        # 无关键词直接返回空
        if not query:
            return Response({
                "query": query,
                "results": {},
                "total": 0,
                "has_result": False,
            })

        # 如果限定 type，只查单个模型
        if search_type:
            result_list = search_single_type(query, search_type, sort)
            paginator = Paginator(result_list, limit)
            page_obj = paginator.get_page(page)

            return Response({
                "query": query,
                "results": {
                    search_type: list(page_obj),
                },
                "total": paginator.count,
                "has_result": paginator.count > 0,
            })

        # 不限定类型 → 全类型搜索（不混合，按类型返回）
        raw_results = search_all_types(query, sort)

        # 为每个结果添加type字段
        for type_name, items in raw_results.items():
            for item in items:
                item["type"] = type_name

        # 计算总数
        total = sum(len(items) for items in raw_results.values())
        has_result = total > 0

        return Response({
            "query": query,
            "results": raw_results,
            "total": total,
            "has_result": has_result,
        })
    
# 用于在全类型搜索时将各类型结果合并、排序和分页
def combine_and_paginate(raw_results, page, limit, sort):
    """
    all_results 是一个 dict：
      {
        "anime": [...],
        "item": [...],
        "person": [...],
      }
    """
    combined = []
    for type_name, items in raw_results.items():
        for item in items:
            item["type"] = type_name
            combined.append(item)

    if sort == "relevance":
        combined.sort(key=lambda x: x["related_score"], reverse=True)
    elif sort == "popularity":
        combined.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    elif sort == "time":
        combined.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    paginator = Paginator(combined, limit)
    page_obj = paginator.get_page(page)

    return {
        "list": list(page_obj),
        "total": paginator.count,
    }

