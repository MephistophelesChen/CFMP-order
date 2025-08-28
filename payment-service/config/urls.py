"""
URL configuration for payment service project.
完全兼容原有交易模块API路径
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 支付接口 - 兼容原有 /api/payment/ 路径
    path('api/payment/', include('payment.urls')),
]
