"""
支付服务视图 - 微服务版本
解耦改造：移除对Order和User的直接依赖，通过微服务API通信
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
from common.service_client import service_client
import uuid
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentCreateAPIView(CreateAPIView):
    """创建支付

    微服务通信点：
    1. 验证订单信息：调用OrderService确认订单状态
    2. 创建支付后：调用NotificationService发送支付通知
    """
    serializer_class = CreatePaymentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # 微服务通信：获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        # TODO: 调用OrderService验证订单信息
        order_uuid = request.data.get('order_uuid')
        if order_uuid:
            # order_data = service_client.get('OrderService', f'/api/orders/{order_uuid}/')
            # if not order_data:
            #     return Response({'error': '订单不存在'}, status=status.HTTP_400_BAD_REQUEST)
            # if order_data.get('status') != 0:  # 只能支付待支付的订单
            #     return Response({'error': '订单状态不允许支付'}, status=status.HTTP_400_BAD_REQUEST)
            # if order_data.get('buyer_uuid') != user_uuid:
            #     return Response({'error': '订单不属于当前用户'}, status=status.HTTP_403_FORBIDDEN)
            pass

        serializer = self.get_serializer(
            data=request.data,
            context={'user_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # TODO: 调用NotificationService发送支付创建通知
        # try:
        #     service_client.post('NotificationService', '/api/notifications/', {
        #         'user_uuid': user_uuid,
        #         'type': 0,  # transaction
        #         'title': '支付订单已创建',
        #         'content': f'订单支付已创建，金额：¥{payment.amount}，请及时完成支付',
        #         'related_id': str(payment.payment_uuid)
        #     })
        # except Exception as e:
        #     logger.warning(f"发送支付创建通知失败: {e}")

        # 返回支付信息
        response_serializer = PaymentSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def _get_user_uuid_from_request(self):
        """从请求中获取用户UUID"""
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: 调用UserService验证token
            pass

        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user_id = getattr(self.request.user, 'pk', None)
            return getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None

        logger.warning("无法获取用户UUID，使用默认值进行开发测试")
        return str(uuid.uuid4())
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


class PaymentQueryByOrderAPIView(GenericAPIView):
    """通过订单ID查询支付信息 - 兼容原有API /api/payment/{order_id}/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        # 通过订单ID查询支付记录
        try:
            payment = Payment.objects.filter(
                order_id=order_id,
                user_uuid=user_uuid
            ).latest('created_at')

            serializer = PaymentSerializer(payment)
            return Response({
                'code': '200',
                'message': 'success',
                'data': serializer.data
            })
        except Payment.DoesNotExist:
            return Response({
                'code': '404',
                'message': '未找到该订单的支付记录',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)


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

        return Response({
            'code': '200',
            'message': '支付已取消',
            'data': None
        })


class PaymentRefundAPIView(GenericAPIView):
    """订单退款API - 供OrderService调用"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        """处理订单退款"""
        refund_amount = request.data.get('refund_amount')
        refund_reason = request.data.get('refund_reason', '订单取消')
        refund_method = request.data.get('refund_method', 'original_payment')

        try:
            # 查找该订单的支付记录
            payment = Payment.objects.filter(
                order_id=order_id,
                status=1  # 已支付
            ).latest('created_at')

            if not payment:
                return Response({
                    'code': '404',
                    'message': '未找到该订单的支付记录',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)

            # 验证退款金额
            if refund_amount and float(refund_amount) > float(payment.amount):
                return Response({
                    'code': '400',
                    'message': '退款金额不能超过支付金额',
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)

            actual_refund_amount = refund_amount or payment.amount

            # TODO: 调用第三方支付平台进行退款
            # refund_result = third_party_refund(payment.payment_method, payment.transaction_id, actual_refund_amount)

            # 创建退款记录
            refund_payment = Payment.objects.create(
                payment_uuid=uuid.uuid4(),
                order_id=order_id,
                user_uuid=payment.user_uuid,
                amount=-float(actual_refund_amount),  # 负数表示退款
                payment_method=payment.payment_method,
                status=1,  # 退款成功
                transaction_id=f"REFUND_{payment.transaction_id}",
                callback_data={'refund_reason': refund_reason, 'original_payment': str(payment.payment_uuid)}
            )

            # 更新原支付记录状态
            payment.status = 4  # 已退款
            payment.save()

            return Response({
                'code': '200',
                'message': '退款处理成功',
                'data': {
                    'success': True,
                    'refund_id': str(refund_payment.payment_uuid),
                    'order_id': order_id,
                    'refund_amount': float(actual_refund_amount),
                    'refund_status': 'completed',
                    'estimated_arrival': '3-5个工作日'
                }
            })

        except Payment.DoesNotExist:
            return Response({
                'code': '404',
                'message': '未找到该订单的支付记录',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"退款处理失败: {e}")
            return Response({
                'code': '500',
                'message': '退款处理失败，请稍后重试',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
