"""
支付服务模型
"""
from django.db import models
import uuid


# 支付方式常量
PAYMENT_METHOD_CHOICES = (
    (0, 'alipay'),       # 支付宝支付
    (1, 'wechat_pay'),   # 微信支付
)

# 支付状态常量
PAYMENT_STATUS_CHOICES = (
    (0, 'pending'),      # 待支付
    (1, 'processing'),   # 处理中
    (2, 'success'),      # 成功
    (3, 'failed'),       # 失败
    (4, 'cancelled'),    # 已取消
)


class Payment(models.Model):
    """支付记录"""
    payment_id = models.AutoField(primary_key=True)
    payment_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # 解耦改造：使用UUID替代外键
    order_uuid = models.UUIDField()  # 订单UUID
    user_uuid = models.UUIDField()   # 用户UUID

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.SmallIntegerField(choices=PAYMENT_METHOD_CHOICES)
    status = models.SmallIntegerField(choices=PAYMENT_STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    # transaction_id = models.BigIntegerField(null=True, blank=True)  # 支付平台交易号 - 暂时不使用
    payment_subject = models.CharField(max_length=255)  # 支付标题
    payment_data = models.JSONField(default=dict, blank=True)  # 支付数据（如支付URL、二维码等）
    failure_reason = models.CharField(max_length=255, null=True, blank=True)

    # 支付回调相关
    callback_received = models.BooleanField(default=False)
    callback_data = models.JSONField(default=dict, blank=True)
    callback_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.payment_id}"

    class Meta:
        db_table = "payment"
        ordering = ['-created_at']
