"""
通知服务序列化器
"""
from rest_framework import serializers
from .models import Notification, SecurityPolicy, RiskAssessment, NOTIFICATION_TYPE_CHOICES, get_notification_type_value
import sys
import os

# 添加公共模块路径（用于从各微服务导入 common）
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

from common.service_client import service_client


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
        """获取用户信息：调用 UserService API /api/v1/user/

        兼容策略：若失败，返回最小占位信息。
        """
        user_uuid = str(obj.user_uuid)
        try:
            resp = service_client.get('UserService', f'/api/v1/user/{user_uuid}/')
            data = (resp or {}).get('data') or None
            if data:
                return {
                    'user_id': data.get('user_id') or data.get('id') or user_uuid,
                    'username': data.get('username') or data.get('name') or '用户'
                }
        except Exception as e:
            print(f"获取用户信息失败: {e}")

        # 兜底占位（避免前端空指针）
        return {
            'user_id': user_uuid,
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

    def validate_type(self, value):
        """验证并转换通知类型"""
        converted_type = get_notification_type_value(value)
        if converted_type is None:
            raise serializers.ValidationError(f"无效的通知类型: {value}. 支持的类型: transaction, system, promotion 或 0, 1, 2")
        return converted_type


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
