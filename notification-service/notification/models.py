"""
通知服务模型
"""
from django.db import models
import uuid


# 通知类型常量
NOTIFICATION_TYPE_CHOICES = (
    (0, 'transaction'),  # 交易通知
    (1, 'system'),       # 系统通知
    (2, 'promotion'),    # 促销通知
)

def get_notification_type_value(type_input):
    """将通知类型字符串转换为数据库存储的整数值"""
    if isinstance(type_input, int):
        return type_input if type_input in [0, 1, 2] else None
    
    if isinstance(type_input, str):
        type_mapping = {
            'transaction': 0,
            'system': 1,
            'promotion': 2
        }
        # 尝试字符串映射
        if type_input.lower() in type_mapping:
            return type_mapping[type_input.lower()]
        
        # 尝试转换为整数
        try:
            type_int = int(type_input)
            return type_int if type_int in [0, 1, 2] else None
        except (ValueError, TypeError):
            return None
    
    return None


class Notification(models.Model):
    """通知"""
    id = models.AutoField(primary_key=True)
    notification_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # 解耦改造：使用UUID替代外键
    user_uuid = models.UUIDField()  # 用户UUID

    type = models.SmallIntegerField(choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    content = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # 关联数据
    related_id = models.CharField(max_length=50, null=True, blank=True)  # 关联的订单ID、支付ID等
    related_data = models.JSONField(default=dict, null=True, blank=True)  # 附加数据

    def __str__(self):
        return self.title

    class Meta:
        db_table = "notification"
        ordering = ['-created_at']


class SecurityPolicy(models.Model):
    """安全策略"""
    policy_id = models.IntegerField(primary_key=True)
    policy_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    policy_name = models.CharField(max_length=100)
    policy_description = models.TextField()
    is_enabled = models.BooleanField(default=True)
    security_level = models.CharField(max_length=20, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ), default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 策略配置
    config_data = models.JSONField(default=dict)  # 策略具体配置

    def __str__(self):
        return self.policy_name

    class Meta:
        db_table = "security_policy"


class RiskAssessment(models.Model):
    """风险评估记录"""
    assessment_id = models.AutoField(primary_key=True)
    assessment_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    user_uuid = models.UUIDField()  # 被评估的用户
    order_uuid = models.UUIDField(null=True, blank=True)  # 相关订单

    risk_score = models.FloatField()  # 风险评分 0-100
    risk_level = models.CharField(max_length=20, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ))

    assessment_data = models.JSONField(default=dict)  # 评估详细数据
    created_at = models.DateTimeField(auto_now_add=True)

    # 处理状态
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(null=True, blank=True)  # 采取的措施

    class Meta:
        db_table = "risk_assessment"
        ordering = ['-created_at']
