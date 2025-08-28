"""
订单服务序列化器 - 微服务版本
"""
from rest_framework import serializers
from .models import Order, OrderItem, PAYMENT_METHOD_CHOICES
import sys
import os

# 添加公共模块路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'common')
sys.path.insert(0, COMMON_DIR)

try:
    from common.service_client import service_client
except ImportError:
    # 如果无法导入，创建一个模拟的客户端
    class MockServiceClient:
        def get(self, service_name, path):
            # TODO: 调用其他微服务API（用户服务、商品服务等）
            return None
    service_client = MockServiceClient()


class OrderItemSerializer(serializers.ModelSerializer):
    """订单项序列化器"""
    product_id = serializers.CharField(source='product_uuid', read_only=True)
    product_name = serializers.CharField(read_only=True)
    product_image = serializers.URLField(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['product_id', 'product_name', 'price', 'quantity', 'product_image']


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器"""
    products = OrderItemSerializer(source='order_items', many=True, read_only=True)
    buyer_info = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'order_uuid', 'total_amount', 'status', 'status_display',
            'created_at', 'updated_at', 'payment_method', 'payment_method_display',
            'payment_time', 'remark', 'products', 'buyer_info'
        ]

    def get_buyer_info(self, obj):
        """通过用户服务获取用户信息"""
        try:
            # TODO: 调用用户服务获取用户信息
            # user_data = service_client.get('user-service', f'/api/users/{obj.buyer_uuid}/')
            # if user_data:
            #     return {
            #         'user_id': user_data.get('user_id'),
            #         'username': user_data.get('username'),
            #         'email': user_data.get('email')
            #     }
            pass
        except Exception as e:
            print(f"获取用户信息失败: {e}")

        return {
            'user_id': str(obj.buyer_uuid),
            'username': '未知用户',
            'email': ''
        }
class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情序列化器"""
    products = OrderItemSerializer(source='order_items', many=True, read_only=True)
    buyer_info = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    # 配送地址解密字段
    shipping_name = serializers.SerializerMethodField()
    shipping_phone = serializers.SerializerMethodField()
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_id', 'order_uuid', 'total_amount', 'status', 'status_display',
            'created_at', 'updated_at', 'payment_method', 'payment_method_display',
            'payment_time', 'remark', 'cancel_reason', 'products', 'buyer_info',
            'shipping_name', 'shipping_phone', 'shipping_address', 'shipping_postal_code'
        ]

    def get_buyer_info(self, obj):
        """通过用户服务获取用户信息"""
        try:
            # TODO: 调用用户服务获取用户信息
            # user_data = service_client.get('user-service', f'/api/users/{obj.buyer_uuid}/')
            # if user_data:
            #     return {
            #         'user_id': user_data.get('user_id'),
            #         'username': user_data.get('username'),
            #         'email': user_data.get('email'),
            #         'phone': user_data.get('phone')
            #     }
            pass
        except Exception as e:
            print(f"获取用户信息失败: {e}")

        return None

    def get_shipping_name(self, obj):
        """解密收货人姓名"""
        # TODO: 实现解密逻辑
        return obj.shipping_name

    def get_shipping_phone(self, obj):
        """解密收货人电话"""
        # TODO: 实现解密逻辑
        return obj.shipping_phone

    def get_shipping_address(self, obj):
        """解密收货地址"""
        # TODO: 实现解密逻辑
        return obj.shipping_address


class CreateOrderSerializer(serializers.Serializer):
    """创建订单序列化器"""
    products = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        help_text="商品列表，格式：[{'product_uuid': 'xxx', 'quantity': 1, 'price': 100.00}]"
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
        buyer_uuid = self.context['buyer_uuid']

        # 计算总金额
        total_amount = sum(
            float(product['price']) * product['quantity']
            for product in products_data
        )

        # 创建订单
        order = Order.objects.create(
            buyer_uuid=buyer_uuid,
            total_amount=total_amount,
            **validated_data
        )

        # 创建订单项
        for product_data in products_data:
            # TODO: 通过商品服务获取商品信息
            # product_info = service_client.get(
            #     'product-service',
            #     f'/api/products/{product_data["product_uuid"]}/'
            # )

            OrderItem.objects.create(
                order=order,
                product_uuid=product_data['product_uuid'],
                product_name='商品名称',  # TODO: 从商品服务获取
                product_price=product_data['price'],
                product_image=None,  # TODO: 从商品服务获取
                price=product_data['price'],
                quantity=product_data['quantity']
            )

        return order
