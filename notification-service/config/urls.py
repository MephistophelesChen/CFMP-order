"""
URL configuration for notification service project.
完全兼容原有交易模块API路径
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 通知和安全策略接口 - 兼容原有 /api/notifications/ 和 /api/security/ 路径
    path('api/', include('notification.urls')),
]
