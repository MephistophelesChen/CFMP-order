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


urlpatterns = [
    # 通知接口
    path('notifications/', include(notification_urlpatterns)),

    # 内部微服务通信接口
    path('internal/notifications/create/', views.NotificationCreateAPIView.as_view(), name='notification-create-internal'),
]
