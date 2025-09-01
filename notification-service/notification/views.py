"""
通知服务视图 - 微服务版本
使用Spring Cloud Gateway解析的用户UUID，避免调用UserService
"""
import uuid
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, GenericAPIView, UpdateAPIView, CreateAPIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Notification, SecurityPolicy, RiskAssessment
from .serializers import (
    NotificationSerializer, SecurityPolicySerializer,
    RiskAssessmentSerializer, CreateNotificationSerializer
)
from common.service_client import service_client
from common.microservice_base import MicroserviceBaseView
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListAPIView(ListAPIView, MicroserviceBaseView):
    """通知列表

    微服务通信点：验证用户身份，获取用户相关通知
    """
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
    # 微服务通信：从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Notification.objects.none()

        queryset = Notification.objects.filter(user_uuid=user_uuid)

        # 筛选条件
        notification_type = getattr(self.request, 'query_params', self.request.GET).get('type')
        if notification_type:
            queryset = queryset.filter(type=notification_type)

        read_status = getattr(self.request, 'query_params', self.request.GET).get('read')
        if read_status == 'true':
            queryset = queryset.filter(read=True)
        elif read_status == 'false':
            queryset = queryset.filter(read=False)

        return queryset.order_by('-created_at')


class NotificationCreateAPIView(CreateAPIView):
    """创建通知（供其他微服务调用）

    微服务通信点：接收其他服务的通知创建请求
    """
    serializer_class = CreateNotificationSerializer
    # permission_classes = [AllowAny]  # 内部微服务调用，暂不需要用户认证

    def create(self, request, *args, **kwargs):
        """创建通知 - 供OrderService、PaymentService等调用"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 验证用户UUID是否有效（可选）
        user_uuid = serializer.validated_data.get('user_uuid')
        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{user_uuid}/')
            if not user_data:
                return Response({'error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            # 外部服务不可用时，降级为跳过校验
            pass

        notification = serializer.save()

        # TODO: 如果启用实时推送，可在此处调用推送服务
        # self._send_real_time_notification(notification)

        response_serializer = NotificationSerializer(notification)
        return Response({
            'code': '200',
            'message': '通知创建成功',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    def _send_real_time_notification(self, notification):
        """发送实时通知（WebSocket、推送等）"""
        # TODO: 实现实时通知推送逻辑
        logger.info(f"发送实时通知: {notification.title} to {notification.user_uuid}")
        pass


class NotificationMarkReadAPIView(GenericAPIView, MicroserviceBaseView):
    """标记通知为已读"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user_uuid=user_uuid
        )

        if not notification.read:
            notification.read = True
            notification.read_at = timezone.now()
            notification.save()

        return Response({'message': '已标记为已读'})


class NotificationMarkAllReadAPIView(GenericAPIView, MicroserviceBaseView):
    """标记所有通知为已读"""
    # permission_classes = [IsAuthenticated]

    def post(self, request):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        unread_notifications = Notification.objects.filter(
            user_uuid=user_uuid,
            read=False
        )

        count = unread_notifications.count()
        unread_notifications.update(
            read=True,
            read_at=timezone.now()
        )

        return Response({'message': f'已标记{count}条通知为已读'})


class NotificationUnreadCountAPIView(GenericAPIView, MicroserviceBaseView):
    """获取未读通知数量"""
    # permission_classes = [IsAuthenticated]

    def get(self, request):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        unread_count = Notification.objects.filter(
            user_uuid=user_uuid,
            read=False
        ).count()

        return Response({'unread_count': unread_count})


class NotificationDetailAPIView(GenericAPIView, MicroserviceBaseView):
    """通知详情 - 兼容原有API GET/DELETE /api/notifications/{notification_id}/"""
    # permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        """获取通知详情"""
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user_uuid=user_uuid
        )

        serializer = NotificationSerializer(notification)
        return Response({
            'code': '200',
            'message': 'success',
            'data': serializer.data
        })

    def delete(self, request, notification_id):
        """删除通知"""
        # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user_uuid=user_uuid
        )

        notification.delete()
        return Response({
            'code': '200',
            'message': '通知已删除',
            'data': None
        })


class NotificationDeleteAPIView(GenericAPIView, MicroserviceBaseView):
    """删除通知"""
    # permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user_uuid=user_uuid
        )

        notification.delete()
        return Response({'message': '通知已删除'})
