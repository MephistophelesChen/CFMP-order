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
from .models import Notification, SecurityPolicy, RiskAssessment, get_notification_type_value

# 添加公共模块路径 - 必须在导入 serializers 之前
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 正确的做法：添加包含 common 目录的父目录
PARENT_DIR = os.path.dirname(BASE_DIR)

if not os.path.exists(os.path.join(PARENT_DIR, 'common')):
    raise FileNotFoundError(
        f"无法找到 common 配置目录。已尝试路径: {os.path.join(PARENT_DIR, 'common')}\n"
        f"请确保 common 目录存在于正确位置。"
    )

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# 现在可以安全地导入依赖 common 模块的 serializers
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
            # 转换字符串类型为整数值
            type_value = get_notification_type_value(notification_type)
            if type_value is not None:
                queryset = queryset.filter(type=type_value)
            else:
                logger.warning(f"无效的通知类型参数: {notification_type}")
                # 无效类型，返回空查询集
                return Notification.objects.none()

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
        # 临时调试：记录所有相关的请求头信息
        headers_to_check = [
            'UUID', 'HTTP_UUID', 'HTTP_X_USER_UUID', 'HTTP_X_USER_ID',
            'HTTP_USER_UUID', 'HTTP_USER_ID', 'HTTP_AUTHORIZATION'
        ]
        header_info = {h: request.META.get(h, 'Not found') for h in headers_to_check}
        logger.info(f"NotificationDetail Headers: {header_info}")

    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        logger.info(f"Retrieved user_uuid: {user_uuid}")
        if not user_uuid:
            logger.warning(f"用户UUID获取失败 - notification_id: {notification_id}")
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
