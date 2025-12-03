from django.urls import path
from wangumi_app.views.search_view import SearchView

urlpatterns = [
    path("search/", SearchView.as_view(), name="search"),
]
