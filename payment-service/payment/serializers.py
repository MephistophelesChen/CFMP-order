"""
支付服务序列化器
"""
from rest_framework import serializers
from .models import Payment, PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
import sys
import os

# 添加公共模块路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMON_DIR = os.path.join(os.path.dirname(BASE_DIR), 'common')
sys.path.insert(0, COMMON_DIR)

try:
    from common.service_client import service_client
except ImportError:
    class MockServiceClient:
        def get(self, service_name, path):
            # TODO: 调用其他微服务API（订单服务、用户服务等）
            return None
    service_client = MockServiceClient()


class PaymentSerializer(serializers.ModelSerializer):
    """支付记录序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    order_info = serializers.SerializerMethodField(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'payment_id', 'payment_uuid', 'order_uuid', 'user_uuid',
            'amount', 'payment_method', 'payment_method_display',
            'status', 'status_display', 'created_at', 'paid_at',
            'expires_at', 'transaction_id', 'payment_subject',
            'payment_data', 'failure_reason', 'order_info', 'user_info'
        ]

    def get_order_info(self, obj):
        """获取订单信息"""
        try:
            # TODO: 调用订单服务获取订单信息
            # order_data = service_client.get('order-service', f'/api/orders/{obj.order_uuid}/')
            # if order_data:
            #     return {
            #         'order_id': order_data.get('order_id'),
            #         'total_amount': order_data.get('total_amount'),
            #         'status': order_data.get('status')
            #     }
            pass
        except Exception as e:
            print(f"获取订单信息失败: {e}")
        return None

    def get_user_info(self, obj):
        """获取用户信息"""
        try:
            # TODO: 调用用户服务获取用户信息
            # user_data = service_client.get('user-service', f'/api/users/{obj.user_uuid}/')
            # if user_data:
            #     return {
            #         'user_id': user_data.get('user_id'),
            #         'username': user_data.get('username')
            #     }
            pass
        except Exception as e:
            print(f"获取用户信息失败: {e}")
        return None


class CreatePaymentSerializer(serializers.Serializer):
    """创建支付序列化器"""
    order_uuid = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=PAYMENT_METHOD_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_subject = serializers.CharField(max_length=255)

    def validate_order_uuid(self, value):
        """验证订单UUID"""
        # TODO: 调用订单服务验证订单是否存在且状态正确
        # order_data = service_client.get('order-service', f'/api/orders/{value}/')
        # if not order_data:
        #     raise serializers.ValidationError("订单不存在")
        # if order_data.get('status') != 0:  # 待支付状态
        #     raise serializers.ValidationError("订单状态不正确")
        return value

    def create(self, validated_data):
        """创建支付记录"""
        user_uuid = self.context['user_uuid']

        payment = Payment.objects.create(
            user_uuid=user_uuid,
            **validated_data
        )

        # TODO: 调用第三方支付接口生成支付数据
        # 这里模拟生成支付数据
        payment.payment_data = {
            'qr_code': f'https://payment.example.com/qr/{payment.payment_uuid}',
            'payment_url': f'https://payment.example.com/pay/{payment.payment_uuid}'
        }
        payment.save()

        return payment


class PaymentCallbackSerializer(serializers.Serializer):
    """支付回调序列化器"""
    payment_uuid = serializers.UUIDField()
    transaction_id = serializers.CharField()
    status = serializers.ChoiceField(choices=PAYMENT_STATUS_CHOICES)
    callback_data = serializers.JSONField(required=False)
