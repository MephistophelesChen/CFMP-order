"""
订单服务模型 - 解耦后的版本
只包含订单相关的核心数据，移除了对User和Product的外键依赖
"""
from django.db import models
import uuid


# 订单状态常量
ORDER_STATUS_CHOICES = (
    (0, 'pending_payment'),  # 待支付
    (1, 'paid'),           # 已支付
    (2, 'completed'),      # 已完成
    (3, 'cancelled'),      # 已取消
)

# 支付方式常量
PAYMENT_METHOD_CHOICES = (
    (0, 'alipay'),       # 支付宝支付
    (1, 'wechat_pay'),   # 微信支付
)


class Order(models.Model):
    """订单模型 - 微服务版本"""
    order_id = models.AutoField(primary_key=True)
    order_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # 解耦改造：使用UUID替代外键
    buyer_uuid = models.UUIDField()  # 用户UUID，通过API调用用户服务获取用户信息
    seller_uuid = models.UUIDField(null=True, blank=True)  # 卖家UUID，通过API调用用户服务获取用户信息
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.SmallIntegerField(choices=ORDER_STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_method = models.SmallIntegerField(choices=PAYMENT_METHOD_CHOICES, null=True, blank=True)
    payment_time = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(blank=True, null=True)
    cancel_reason = models.TextField(blank=True, null=True)

    # 配送地址信息（加密存储）
    shipping_name = models.CharField(max_length=500, null=True, blank=True)
    shipping_phone = models.CharField(max_length=200, null=True, blank=True)
    shipping_address = models.TextField(null=True, blank=True)
    shipping_postal_code = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id}"

    class Meta:
        db_table = "order"
        ordering = ['-created_at']


class OrderItem(models.Model):
    """订单商品项 - 微服务版本"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')

    # 解耦改造：使用UUID替代外键
    product_uuid = models.UUIDField()  # 商品UUID，通过API调用商品服务获取商品信息

    # 冗余商品信息（下单时快照）
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_image = models.URLField(null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)  # 实际成交价
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "order_item"

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
