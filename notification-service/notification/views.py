"""
通知服务视图 - 微服务版本
解耦改造：移除对User的直接依赖，通过微服务API通信
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
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListAPIView(ListAPIView):
    """通知列表

    微服务通信点：验证用户身份，获取用户相关通知
    """
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 微服务通信：从认证头获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
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

    def _get_user_uuid_from_request(self):
        """从请求中获取用户UUID"""
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: 调用UserService验证token
            # user_data = service_client.post('UserService', '/api/auth/verify-token/',
            #                               {'token': token})
            # return user_data.get('user_uuid') if user_data else None
            pass

        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user_id = getattr(self.request.user, 'pk', None)
            return getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None

        logger.warning("无法获取用户UUID，使用默认值进行开发测试")
        return str(uuid.uuid4())


class NotificationCreateAPIView(CreateAPIView):
    """创建通知（供其他微服务调用）

    微服务通信点：接收其他服务的通知创建请求
    """
    serializer_class = CreateNotificationSerializer
    permission_classes = [AllowAny]  # 内部微服务调用，暂不需要用户认证

    def create(self, request, *args, **kwargs):
        """创建通知 - 供OrderService、PaymentService等调用"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 验证用户UUID是否有效（可选）
        user_uuid = serializer.validated_data.get('user_uuid')
        # TODO: 调用UserService验证用户是否存在
        # user_data = service_client.get('UserService', f'/api/users/{user_uuid}/')
        # if not user_data:
        #     return Response({'error': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)

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


class NotificationMarkReadAPIView(GenericAPIView):
    """标记通知为已读"""
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

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


class NotificationMarkAllReadAPIView(GenericAPIView):
    """标记所有通知为已读"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

        unread_notifications = Notification.objects.filter(
            user_uuid=user_uuid,
            read=False
        )

        unread_notifications.update(
            read=True,
            read_at=timezone.now()
        )

        return Response({'message': f'已标记{unread_notifications.count()}条通知为已读'})


class NotificationUnreadCountAPIView(GenericAPIView):
    """获取未读通知数量"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

        unread_count = Notification.objects.filter(
            user_uuid=user_uuid,
            read=False
        ).count()

        return Response({'unread_count': unread_count})


class NotificationDetailAPIView(GenericAPIView):
    """通知详情 - 兼容原有API GET/DELETE /api/notifications/{notification_id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, notification_id):
        """获取通知详情"""
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

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
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

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


class NotificationDeleteAPIView(GenericAPIView):
    """删除通知"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, notification_id):
        # TODO: 从JWT token获取用户UUID
        user_uuid = request.user.id

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user_uuid=user_uuid
        )

        notification.delete()
        return Response({'message': '通知已删除'})


class SecurityPolicyListAPIView(ListAPIView):
    """安全策略列表"""
    queryset = SecurityPolicy.objects.filter(is_enabled=True)
    serializer_class = SecurityPolicySerializer
    permission_classes = [IsAdminUser]


class SecurityPolicyUpdateAPIView(UpdateAPIView):
    """更新安全策略"""
    queryset = SecurityPolicy.objects.all()
    serializer_class = SecurityPolicySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'policy_id'


class RiskAssessmentAPIView(GenericAPIView):
    """风险评估"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """执行风险评估"""
        user_uuid = request.data.get('user_uuid')
        order_uuid = request.data.get('order_uuid')

        if not user_uuid:
            # TODO: 从JWT token获取用户UUID
            user_uuid = request.user.id

        # TODO: 实现风险评估算法
        risk_score = self._calculate_risk_score(user_uuid, order_uuid)
        risk_level = self._get_risk_level(risk_score)

        # 创建评估记录
        assessment = RiskAssessment.objects.create(
            user_uuid=user_uuid,
            order_uuid=order_uuid,
            risk_score=risk_score,
            risk_level=risk_level,
            assessment_data={
                'factors': ['payment_history', 'order_frequency', 'amount_analysis'],
                'details': '风险评估详细信息'
            }
        )

        serializer = RiskAssessmentSerializer(assessment)
        return Response(serializer.data)

    def _calculate_risk_score(self, user_uuid, order_uuid):
        """计算风险评分"""
        # TODO: 实现具体的风险评估算法
        # 这里返回模拟数据
        import random
        return round(random.uniform(0, 100), 2)

    def _get_risk_level(self, score):
        """根据评分获取风险等级"""
        if score < 25:
            return 'low'
        elif score < 50:
            return 'medium'
        elif score < 75:
            return 'high'
        else:
            return 'critical'


class FraudDetectionAPIView(GenericAPIView):
    """欺诈检测"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """执行欺诈检测"""
        user_uuid = request.data.get('user_uuid')
        order_data = request.data.get('order_data', {})

        if not user_uuid:
            # TODO: 从JWT token获取用户UUID
            user_uuid = request.user.id

        # TODO: 实现欺诈检测算法
        is_fraud = self._detect_fraud(user_uuid, order_data)
        confidence = self._get_confidence_score(user_uuid, order_data)

        result = {
            'is_fraud': is_fraud,
            'confidence': confidence,
            'reasons': ['异常交易时间', '金额超出正常范围'] if is_fraud else [],
            'recommended_action': 'block' if is_fraud and confidence > 0.8 else 'review'
        }

        return Response(result)

    def _detect_fraud(self, user_uuid, order_data):
        """检测是否为欺诈"""
        # TODO: 实现具体的欺诈检测算法
        import random
        return random.choice([True, False])

    def _get_confidence_score(self, user_uuid, order_data):
        """获取置信度评分"""
        # TODO: 实现置信度计算
        import random
        return round(random.uniform(0, 1), 2)
