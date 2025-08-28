"""
支付服务URL配置 - 完全兼容原有 /api/payment/ 接口
"""
from django.urls import path
from . import views

urlpatterns = [
    # 支付接口 - 完全兼容原有API路径 /api/payment/
    path('create/', views.PaymentCreateAPIView.as_view(), name='payment-create'),  # POST /api/payment/create/
    path('callback/<str:payment_method>/', views.PaymentCallbackAPIView.as_view(), name='payment-callback'),  # GET/POST /api/payment/callback/{payment_method}/
    path('<str:order_id>/', views.PaymentQueryByOrderAPIView.as_view(), name='payment-query-by-order'),  # GET /api/payment/{order_id}/
    path('records/', views.PaymentRecordsAPIView.as_view(), name='payment-records'),  # GET /api/payment/records/
    path('<uuid:payment_id>/cancel/', views.PaymentCancelAPIView.as_view(), name='payment-cancel'),  # POST /api/payment/{payment_id}/cancel/

    # 新增：订单退款API - 供OrderService调用
    path('<str:order_id>/refund/', views.PaymentRefundAPIView.as_view(), name='payment-refund'),  # POST /api/payment/{order_id}/refund/
]
