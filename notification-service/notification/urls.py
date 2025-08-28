"""
通知服务URL配置
"""
from django.urls import path
from . import views

urlpatterns = [
    # 通知相关路由
    path('notifications/', views.NotificationListAPIView.as_view(), name='notification-list'),
    path('notifications/create/', views.NotificationCreateAPIView.as_view(), name='notification-create'),
    path('notifications/<int:notification_id>/read/', views.NotificationMarkReadAPIView.as_view(), name='notification-mark-read'),
    path('notifications/read-all/', views.NotificationMarkAllReadAPIView.as_view(), name='notification-read-all'),
    path('notifications/unread-count/', views.NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),
    path('notifications/<int:notification_id>/', views.NotificationDeleteAPIView.as_view(), name='notification-delete'),

    # 安全策略相关路由
    path('security/policies/', views.SecurityPolicyListAPIView.as_view(), name='security-policies-list'),
    path('security/policies/<int:policy_id>/', views.SecurityPolicyUpdateAPIView.as_view(), name='security-policies-update'),
    path('security/risk-assessment/', views.RiskAssessmentAPIView.as_view(), name='security-risk-assessment'),
    path('security/fraud-detection/', views.FraudDetectionAPIView.as_view(), name='security-fraud-detection'),
]
