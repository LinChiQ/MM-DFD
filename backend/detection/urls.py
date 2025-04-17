"""
检测应用URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DetectionViewSet

router = DefaultRouter()
router.register(r'', DetectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
