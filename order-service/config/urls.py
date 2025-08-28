"""
URL configuration for order service project.
完全兼容原有交易模块API路径
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 订单管理接口 - 兼容原有 /api/orders/ 路径
    path('api/orders/', include('order.urls')),
]
