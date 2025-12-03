import importlib
import os
from django.urls import path, include

urlpatterns = []

current_dir = os.path.dirname(__file__)
for filename in os.listdir(current_dir):
    if filename.endswith("_url.py") and filename != "__init__.py":
        module_name = f"wangumi_app.urls.{filename[:-3]}"
        module = importlib.import_module(module_name)
        urlpatterns += getattr(module, "urlpatterns", [])
