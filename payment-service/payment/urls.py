"""
支付服务URL配置 - 完全兼容原有 /api/payment/ 接口
"""
from django.urls import path
from . import views

urlpatterns = [
    # 支付接口 - 完全兼容原有API路径 /api/payment/
    path('create/', views.PaymentCreateAPIView.as_view(), name='payment-create'),  # POST /api/payment/create/
    path('callback/<str:payment_method>/', views.PaymentCallbackAPIView.as_view(), name='payment-callback'),  # GET/POST /api/payment/callback/{payment_method}/
    path('records/', views.PaymentRecordsAPIView.as_view(), name='payment-records'),  # GET /api/payment/records/
    path('<uuid:order_uuid>/', views.PaymentQueryByOrderAPIView.as_view(), name='payment-query-by-order'),  # GET /api/payment/{order_uuid}/
    path('<uuid:payment_uuid>/cancel/', views.PaymentCancelAPIView.as_view(), name='payment-cancel'),  # POST /api/payment/{payment_uuid}/cancel/

    # 新增：订单退款API - 供OrderService调用
    path('<uuid:order_uuid>/refund/', views.PaymentRefundAPIView.as_view(), name='payment-refund'),  # POST /api/payment/{order_uuid}/refund/
]
