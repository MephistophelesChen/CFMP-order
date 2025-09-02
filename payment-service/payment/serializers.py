"""
支付服务序列化器
"""
from rest_framework import serializers
from .models import Payment, PAYMENT_METHOD_CHOICES, PAYMENT_STATUS_CHOICES
import sys
import os

# 添加公共模块路径
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
            # 调用订单服务内部接口获取订单详情
            resp = service_client.get('OrderService', f'/api/orders/internal/{obj.order_uuid}/')
            if resp and resp.get('success') and resp.get('data'):
                data = resp.get('data') or {}
                return {
                    'order_id': data.get('order_id'),
                    'total_amount': data.get('total_amount'),
                    'status': data.get('status')
                }
        except Exception as e:
            print(f"获取订单信息失败: {e}")
        return None

    def get_user_info(self, obj):
        """获取用户信息：调用 UserService API /api/v1/user/

        兼容策略：失败时返回 None，调用方可忽略此字段。
        """
        try:
            resp = service_client.get('UserService', f'/api/v1/user/{obj.user_uuid}/')
            data = (resp or {}).get('data') or None
            if data:
                return {
                    'user_id': data.get('user_id') or data.get('id') or str(obj.user_uuid),
                    'username': data.get('username') or data.get('name') or '用户'
                }
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
        # 调用订单服务内部接口验证订单是否存在且状态为待支付
        try:
            resp = service_client.get('OrderService', f'/api/orders/internal/{value}/')
            if not resp or not resp.get('success'):
                raise serializers.ValidationError("订单不存在")
            data = resp.get('data') or {}
            if data.get('status') != 0:  # 待支付状态
                raise serializers.ValidationError("订单状态不正确")
        except serializers.ValidationError:
            raise
        except Exception as e:
            # 无法联系订单服务时，返回验证失败
            raise serializers.ValidationError("订单验证失败")
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
