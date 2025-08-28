"""
订单服务URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 订单相关路由
    path('orders/', views.OrderListCreateAPIView.as_view(), name='order-list-create'),
    path('orders/<int:order_id>/', views.OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/cancel/', views.OrderCancelAPIView.as_view(), name='order-cancel'),
    path('orders/<int:order_id>/complete/', views.OrderCompleteAPIView.as_view(), name='order-complete'),
    path('orders/stats/', views.OrderStatsAPIView.as_view(), name='order-stats'),
]
