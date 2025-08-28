"""
支付服务视图
"""
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer, PaymentCallbackSerializer
import uuid


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentCreateAPIView(CreateAPIView):
    """创建支付"""
    serializer_class = CreatePaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        serializer = self.get_serializer(
            data=request.data,
            context={'user_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # 返回支付信息
        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
class PaymentRecordsAPIView(ListAPIView):
    """支付记录列表"""
    serializer_class = PaymentSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(self.request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟
        return Payment.objects.filter(user_uuid=user_uuid)


class PaymentQueryAPIView(GenericAPIView):
    """支付查询"""
    permission_classes = [IsAuthenticated]

    def get(self, request, payment_uuid):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        payment = get_object_or_404(
            Payment,
            payment_uuid=payment_uuid,
            user_uuid=user_uuid
        )

        serializer = PaymentSerializer(payment)
        return Response(serializer.data)


class PaymentCallbackAPIView(GenericAPIView):
    """支付回调处理"""
    permission_classes = [AllowAny]  # 第三方支付平台回调，不需要认证

    def post(self, request, payment_method):
        """处理支付回调"""
        # TODO: 验证回调签名

        serializer = PaymentCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取验证后的数据
        payment_uuid = request.data.get('payment_uuid')
        transaction_id = request.data.get('transaction_id')
        payment_status = request.data.get('status')
        callback_data = request.data.get('callback_data', {})

        try:
            payment = Payment.objects.get(payment_uuid=payment_uuid)

            # 更新支付状态
            payment.status = payment_status
            payment.transaction_id = transaction_id
            payment.callback_received = True
            payment.callback_data = callback_data
            payment.callback_time = timezone.now()

            if payment_status == 2:  # 支付成功
                payment.paid_at = timezone.now()
            elif payment_status in [3, 4]:  # 失败或取消
                payment.failure_reason = callback_data.get('failure_reason', '支付失败')

            payment.save()

            # TODO: 通知订单服务更新订单状态
            # service_client.post('order-service', f'/api/orders/{payment.order_uuid}/payment-callback/', {
            #     'payment_status': payment_status,
            #     'payment_id': payment.payment_id
            # })

            return Response({'message': '回调处理成功'})

        except Payment.DoesNotExist:
            return Response(
                {'error': '支付记录不存在'},
                status=status.HTTP_404_NOT_FOUND
            )


class PaymentCancelAPIView(GenericAPIView):
    """取消支付"""
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_uuid):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        payment = get_object_or_404(
            Payment,
            payment_uuid=payment_uuid,
            user_uuid=user_uuid
        )

        if payment.status not in [0, 1]:  # 只能取消待支付或处理中的支付
            return Response(
                {'error': '该支付无法取消'},
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.status = 4  # 已取消
        payment.failure_reason = '用户主动取消'
        payment.save()

        return Response({'message': '支付已取消'})
