"""
支付服务URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 支付相关路由
    path('payment/create/', views.PaymentCreateAPIView.as_view(), name='payment-create'),
    path('payment/records/', views.PaymentRecordsAPIView.as_view(), name='payment-records'),
    path('payment/<uuid:payment_uuid>/', views.PaymentQueryAPIView.as_view(), name='payment-query'),
    path('payment/<uuid:payment_uuid>/cancel/', views.PaymentCancelAPIView.as_view(), name='payment-cancel'),
    path('payment/callback/<str:payment_method>/', views.PaymentCallbackAPIView.as_view(), name='payment-callback'),
]
