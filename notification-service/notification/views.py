"""
通知服务视图
"""
import uuid
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, GenericAPIView, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import Notification, SecurityPolicy, RiskAssessment
from .serializers import (
    NotificationSerializer, SecurityPolicySerializer,
    RiskAssessmentSerializer, CreateNotificationSerializer
)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListAPIView(ListAPIView):
    """通知列表"""
    serializer_class = NotificationSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(self.request.user, 'id', None) or uuid.uuid4()

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

        return queryset


class NotificationCreateAPIView(GenericAPIView):
    """创建通知（内部服务调用）"""
    serializer_class = CreateNotificationSerializer
    permission_classes = [IsAuthenticated]  # TODO: 改为服务间认证

    def post(self, request):
        """创建通知"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()

        response_serializer = NotificationSerializer(notification)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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
