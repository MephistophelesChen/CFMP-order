"""
订单服务序列化器 - 微服务版本
"""
from rest_framework import serializers
from .models import Order, OrderItem, PAYMENT_METHOD_CHOICES
import sys
import os

# 添加公共模块路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 检测环境：容器环境 vs 本地开发环境
if BASE_DIR.startswith('/app'):
    # Docker 容器环境
    PARENT_DIR = BASE_DIR
else:
    # 本地开发环境
    PARENT_DIR = os.path.dirname(BASE_DIR)

if not os.path.exists(os.path.join(PARENT_DIR, 'common')):
    raise FileNotFoundError(
        f"无法找到 common 配置目录。已尝试路径: {os.path.join(PARENT_DIR, 'common')}\n"
        f"当前 BASE_DIR: {BASE_DIR}\n"
        f"当前 PARENT_DIR: {PARENT_DIR}\n"
        f"请确保 common 目录存在于正确位置。"
    )

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from common.service_client import service_client


class OrderItemSerializer(serializers.ModelSerializer):
    """订单项序列化器"""
    product_id = serializers.CharField(source='product_uuid', read_only=True)  # 兼容原有API
    product_uuid = serializers.UUIDField(read_only=True)  # 实际UUID
    product_name = serializers.CharField(read_only=True)
    product_image = serializers.URLField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_uuid', 'product_name', 'price', 'quantity', 'product_image']


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器 - 兼容原有API格式"""
    buyer_id = serializers.SerializerMethodField(read_only=True)  # 兼容原有API
    seller_id = serializers.SerializerMethodField(read_only=True)  # 卖家ID
    buyer_uuid = serializers.UUIDField(read_only=True)  # 买家UUID
    seller_uuid = serializers.UUIDField(read_only=True)  # 卖家UUID
    order_uuid = serializers.UUIDField(read_only=True)  # 订单UUID
    products = OrderItemSerializer(source='order_items', many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'order_uuid', 'status', 'created_at', 'payment_method', 'buyer_id', 'seller_id',
            'buyer_uuid', 'seller_uuid', 'cancel_reason', 'payment_time', 'remark',
            'shipping_address', 'shipping_name', 'shipping_phone', 'shipping_postal_code',
            'total_amount', 'updated_at', 'products'
        ]

    def get_buyer_id(self, obj):
        """获取买家ID - 兼容原有API

        微服务通信点：需要通过buyer_uuid调用UserService获取用户ID
        """
        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{obj.buyer_uuid}/')
            if user_data and isinstance(user_data, dict):
                return user_data.get('user_id') or user_data.get('id') or str(obj.buyer_uuid)
        except Exception:
            pass
        # 回退：返回UUID字符串
        return str(obj.buyer_uuid)

    def get_seller_id(self, obj):
        """获取卖家ID - 兼容原有API

        微服务通信点：需要通过seller_uuid调用UserService获取用户ID
        """
        if not obj.seller_uuid:
            return None

        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{obj.seller_uuid}/')
            if user_data and isinstance(user_data, dict):
                return user_data.get('user_id') or user_data.get('id') or str(obj.seller_uuid)
        except Exception:
            pass
        # 回退：返回UUID字符串
        return str(obj.seller_uuid)

    def get_buyer_info(self, obj):
        """通过用户服务获取用户信息"""
        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{obj.buyer_uuid}/')
            if user_data and isinstance(user_data, dict):
                return {
                    'user_id': user_data.get('user_id') or user_data.get('id') or str(obj.buyer_uuid),
                    'username': user_data.get('username') or user_data.get('name') or '',
                    'email': user_data.get('email') or ''
                }
        except Exception as e:
            print(f"获取用户信息失败: {e}")

        return {
            'user_id': str(obj.buyer_uuid),
            'username': '未知用户',
            'email': ''
        }
class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情序列化器 - 兼容原有API格式"""
    buyer_id = serializers.SerializerMethodField(read_only=True)  # 兼容原有API
    seller_id = serializers.SerializerMethodField(read_only=True)  # 卖家ID
    buyer_uuid = serializers.UUIDField(read_only=True)  # 买家UUID
    seller_uuid = serializers.UUIDField(read_only=True)  # 卖家UUID
    order_uuid = serializers.UUIDField(read_only=True)  # 订单UUID
    products = OrderItemSerializer(source='order_items', many=True, read_only=True)

    # 配送地址解密字段
    shipping_name = serializers.SerializerMethodField()
    shipping_phone = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id', 'order_uuid', 'status', 'created_at', 'payment_method', 'buyer_id', 'seller_id',
            'buyer_uuid', 'seller_uuid', 'cancel_reason', 'payment_time', 'remark',
            'shipping_address', 'shipping_name', 'shipping_phone', 'shipping_postal_code',
            'total_amount', 'updated_at', 'products'
        ]

    def get_buyer_id(self, obj):
        """获取买家ID - 兼容原有API"""
        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{obj.buyer_uuid}/')
            if user_data and isinstance(user_data, dict):
                return user_data.get('user_id') or user_data.get('id') or str(obj.buyer_uuid)
        except Exception:
            pass
        return str(obj.buyer_uuid)

    def get_seller_id(self, obj):
        """获取卖家ID - 兼容原有API"""
        if not obj.seller_uuid:
            return None

        try:
            user_data = service_client.get('UserService', f'/api/v1/user/{obj.seller_uuid}/')
            if user_data and isinstance(user_data, dict):
                return user_data.get('user_id') or user_data.get('id') or str(obj.seller_uuid)
        except Exception:
            pass
        return str(obj.seller_uuid)

    def get_shipping_name(self, obj):
        """解密收货人姓名"""
        return obj.shipping_name

    def get_shipping_phone(self, obj):
        """解密收货人电话"""
        return obj.shipping_phone

    def get_shipping_address(self, obj):
        """解密收货地址"""
        return obj.shipping_address


class CreateOrderSerializer(serializers.Serializer):
    """创建订单序列化器"""
    products = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="商品列表，格式：[{'product_uuid': 'xxx', 'quantity': 1, 'price': 100.00}]"
    )
    seller_uuid = serializers.UUIDField(
        write_only=True,
        help_text="卖家UUID"
    )
    payment_method = serializers.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        required=False
    )
    remark = serializers.CharField(max_length=500, required=False, allow_blank=True)

    # 配送地址
    shipping_name = serializers.CharField(max_length=100)
    shipping_phone = serializers.CharField(max_length=20)
    shipping_address = serializers.CharField(max_length=500)
    shipping_postal_code = serializers.CharField(max_length=20, required=False)

    def validate_products(self, value):
        """验证商品数据"""
        if not value:
            raise serializers.ValidationError("商品列表不能为空")

        for product_data in value:
            if 'product_uuid' not in product_data:
                raise serializers.ValidationError("缺少商品UUID")
            if 'quantity' not in product_data or product_data['quantity'] <= 0:
                raise serializers.ValidationError("商品数量必须大于0")
            if 'price' not in product_data or product_data['price'] <= 0:
                raise serializers.ValidationError("商品价格必须大于0")

        return value

    def create(self, validated_data):
        """创建订单"""
        products_data = validated_data.pop('products')
        seller_uuid = validated_data.pop('seller_uuid')  # 获取传入的seller_uuid
        buyer_uuid = self.context['buyer_uuid']

    # TODO(订单冲突检查 - 暂缓实现)：
    # 需求：在创建订单前检查是否已存在“同一买家、未支付、包含相同商品”的订单，避免重复。
    # 推荐实现位置：本方法最前面或视图层（views.create）校验完 serializer.is_valid 之后。
    # 检查维度：buyer_uuid + status==0 + 任一 product_uuid ∈ products_data。
    # 冲突处理：若存在则抛出 serializers.ValidationError 或在视图层返回 400。
    # 当前仅保留注释，不启用以保持现有流程。

        # 计算总金额
        total_amount = sum(
            float(product['price']) * product['quantity']
            for product in products_data
        )

        # 创建订单
        order = Order.objects.create(
            buyer_uuid=buyer_uuid,
            seller_uuid=seller_uuid,  # 使用传入的卖家UUID
            total_amount=total_amount,
            **validated_data
        )

        # 创建订单项
        for product_data in products_data:
            # 通过商品服务获取商品信息（兼容 /api/products/{id}/ 与 /api/product/{id}/）
            product_info = None
            try:
                product_info = service_client.get('ProductService', f"/api/products/{product_data['product_uuid']}/")
                if not product_info:
                    product_info = service_client.get('ProductService', f"/api/product/{product_data['product_uuid']}/")
            except Exception:
                product_info = None

            product_name = None
            product_image = None
            if product_info and isinstance(product_info, dict):
                product_name = product_info.get('name') or product_info.get('title') or '商品'
                product_image = product_info.get('image') or product_info.get('thumbnail')

            OrderItem.objects.create(
                order=order,
                product_uuid=product_data['product_uuid'],
                product_name=product_name or '商品',
                product_price=product_data['price'],
                product_image=product_image,
                price=product_data['price'],
                quantity=product_data['quantity']
            )

        return order
