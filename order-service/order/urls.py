"""
订单服务URL配置 - 完全兼容原有 /api/orders/ 接口
"""
from django.urls import path
from . import views

urlpatterns = [
    # 订单管理接口 - 完全兼容原有API路径 /api/orders/
    path('', views.OrderListCreateAPIView.as_view(), name='order-list-create'),  # GET/POST /api/orders/
    path('<str:order_id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),  # GET/PUT /api/orders/{order_id}/
    path('<str:order_id>/cancel/', views.OrderCancelAPIView.as_view(), name='order-cancel'),  # PUT /api/orders/{order_id}/cancel/
    path('<str:order_id>/complete/', views.OrderCompleteAPIView.as_view(), name='order-complete'),  # PUT /api/orders/{order_id}/complete/
    path('stats/', views.OrderStatsAPIView.as_view(), name='order-stats'),  # GET /api/orders/stats/

    # 微服务内部通信接口
    path('internal/<uuid:order_uuid>/', views.OrderDetailByUUIDAPIView.as_view(), name='order-detail-by-uuid'),
    path('internal/orders/<uuid:order_uuid>/', views.OrderInternalAPIView.as_view(), name='order-internal-api'),
]
