"""
通知服务序列化器
"""
from rest_framework import serializers
from .models import Notification, SecurityPolicy, RiskAssessment, NOTIFICATION_TYPE_CHOICES


class NotificationSerializer(serializers.ModelSerializer):
    """通知序列化器"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_uuid', 'user_uuid', 'type', 'type_display',
            'title', 'content', 'read', 'created_at', 'read_at',
            'related_id', 'related_data', 'user_info'
        ]

    def get_user_info(self, obj):
        """获取用户信息"""
        # TODO: 调用用户服务获取用户信息
        return {
            'user_id': str(obj.user_uuid),
            'username': '用户'
        }


class CreateNotificationSerializer(serializers.ModelSerializer):
    """创建通知序列化器"""

    class Meta:
        model = Notification
        fields = [
            'user_uuid', 'type', 'title', 'content',
            'related_id', 'related_data'
        ]


class SecurityPolicySerializer(serializers.ModelSerializer):
    """安全策略序列化器"""

    class Meta:
        model = SecurityPolicy
        fields = [
            'policy_id', 'policy_uuid', 'policy_name', 'policy_description',
            'is_enabled', 'security_level', 'created_at', 'updated_at',
            'config_data'
        ]


class RiskAssessmentSerializer(serializers.ModelSerializer):
    """风险评估序列化器"""

    class Meta:
        model = RiskAssessment
        fields = [
            'assessment_id', 'assessment_uuid', 'user_uuid', 'order_uuid',
            'risk_score', 'risk_level', 'assessment_data', 'created_at',
            'is_processed', 'processed_at', 'action_taken'
        ]
