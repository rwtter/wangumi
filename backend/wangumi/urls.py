"""
URL configuration for wangumi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView

def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("admin/", admin.site.urls),
    path("api/health", health),
    path("api/", include("wangumi_app.urls")),
]

spa_view = never_cache(TemplateView.as_view(template_name="index.html"))
if settings.DEBUG:#开发模式媒体文件在前
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    re_path(r"^(?!api/|admin/).*", spa_view, name="spa"),
]


