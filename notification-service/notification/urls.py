"""
通知服务URL配置 - 完全兼容原有 /api/notifications/ 和 /api/security/ 接口
"""
from django.urls import path, include
from . import views

# 通知接口URL - 兼容原有 /api/notifications/ 路径
notification_urlpatterns = [
    path('', views.NotificationListAPIView.as_view(), name='notification-list'),  # GET /api/notifications/
    path('<int:notification_id>/', views.NotificationDetailAPIView.as_view(), name='notification-detail'),  # GET/DELETE /api/notifications/{notification_id}/
    path('<int:notification_id>/read/', views.NotificationMarkReadAPIView.as_view(), name='notification-mark-read'),  # PUT /api/notifications/{notification_id}/read/
    path('read-all/', views.NotificationMarkAllReadAPIView.as_view(), name='notification-read-all'),  # PUT /api/notifications/read-all/
    path('unread-count/', views.NotificationUnreadCountAPIView.as_view(), name='notification-unread-count'),  # GET /api/notifications/unread-count/
]

# 安全策略接口URL - 兼容原有 /api/security/ 路径
security_urlpatterns = [
    path('risk-assessment/', views.RiskAssessmentAPIView.as_view(), name='security-risk-assessment'),  # POST /api/security/risk-assessment/
    path('fraud-detection/', views.FraudDetectionAPIView.as_view(), name='security-fraud-detection'),  # POST /api/security/fraud-detection/
    path('policies/', views.SecurityPolicyListAPIView.as_view(), name='security-policies-list'),  # GET/PUT /api/security/policies/
]

urlpatterns = [
    # 通知接口
    path('notifications/', include(notification_urlpatterns)),
    # 安全策略接口
    path('security/', include(security_urlpatterns)),
    
    # 内部微服务通信接口
    path('internal/notifications/create/', views.NotificationCreateAPIView.as_view(), name='notification-create-internal'),
]
