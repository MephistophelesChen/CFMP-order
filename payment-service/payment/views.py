"""
支付服务视图 - 微服务版本
使用Spring Cloud Gateway解析的用户UUID，避免调用UserService
"""
import uuid
import logging
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status as http_status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer, PaymentCallbackSerializer
from common.service_client import service_client
from common.microservice_base import MicroserviceBaseView

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PaymentCreateAPIView(CreateAPIView, MicroserviceBaseView):
    """创建支付

    微服务通信点：
    1. 验证订单信息：调用OrderService确认订单状态
    2. 创建支付后：调用NotificationService发送支付通知
    """
    serializer_class = CreatePaymentSerializer
    # permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
    # 微服务通信：从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=http_status.HTTP_401_UNAUTHORIZED)

        # 调用OrderService验证订单信息（内部接口，免认证）
        order_uuid = request.data.get('order_uuid')
        if order_uuid:
            order_resp = service_client.get('OrderService', f'/api/orders/internal/{order_uuid}/')
            if not order_resp or not order_resp.get('success'):
                return Response({'error': '订单不存在'}, status=http_status.HTTP_400_BAD_REQUEST)
            order_data = order_resp.get('data') or {}
            if order_data.get('status') != 0:  # 只能支付待支付的订单
                return Response({'error': '订单状态不允许支付'}, status=http_status.HTTP_400_BAD_REQUEST)

        # 创建支付记录
        serializer = self.get_serializer(
            data=request.data,
            context={'user_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        # 调用第三方支付接口（模拟）
        payment_result = self._process_payment(payment)

        if payment_result.get('success'):
            # 支付成功：通知订单服务更新状态
            try:
                order_update = {
                    'status': 1,
                    'payment_time': timezone.now().isoformat()
                }
                service_client.patch('OrderService', f'/api/orders/internal/orders/{order_uuid}/', order_update)
            except Exception as e:
                logger.warning(f"更新订单状态失败: {e}")

            # 发送支付成功通知
            try:
                service_client.post('NotificationService', '/api/internal/notifications/create/', {
                    'user_uuid': str(user_uuid),
                    'title': '支付成功',
                    'content': f'订单 {order_uuid} 支付成功，金额 ¥{payment.amount}',
                    'type': 'payment',
                    'related_id': str(order_uuid),
                    'related_data': {
                        'payment_id': payment.payment_id,
                        'amount': str(payment.amount)
                    }
                })
            except Exception as e:
                logger.warning(f"发送支付成功通知失败: {e}")

            response_serializer = PaymentSerializer(payment)
            return Response({
                'code': '200',
                'message': '支付创建成功',
                'data': response_serializer.data
            }, status=http_status.HTTP_201_CREATED)
        else:
            return Response({
                'error': '支付处理失败',
                'details': payment_result.get('error', '未知错误')
            }, status=http_status.HTTP_400_BAD_REQUEST)

    def _process_payment(self, payment):
        """处理支付逻辑"""
        # TODO: 实现具体的支付处理逻辑
        # 这里应该调用支付宝、微信支付等第三方接口

        # 模拟支付处理
        import random
        if random.choice([True, False]):  # 50%成功率模拟
            payment.status = 1  # 支付成功
            payment.transaction_id = f"txn_{uuid.uuid4().hex[:16]}"
            payment.paid_at = timezone.now()
            payment.save()

            return {
                'success': True,
                'transaction_id': payment.transaction_id
            }
        else:
            payment.status = 2  # 支付失败
            payment.save()

            return {
                'success': False,
                'error': '支付处理失败'
            }


class PaymentListAPIView(ListAPIView, MicroserviceBaseView):
    """支付记录列表"""
    serializer_class = PaymentSerializer
    pagination_class = StandardPagination
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Payment.objects.none()

        return Payment.objects.filter(user_uuid=user_uuid).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """返回支付列表 - 兼容原有API响应格式"""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'code': '200',
                'message': 'success',
                'data': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'code': '200',
            'message': 'success',
            'data': serializer.data
        })

class PaymentCallbackAPIView(GenericAPIView):
    """支付回调处理 - 第三方支付平台回调"""
    # permission_classes = [AllowAny]  # 支付回调不需要用户认证

    def post(self, request):
        """处理支付回调"""
        # 为了保持API兼容性，我们支持两种字段名
        payment_id = request.data.get('payment_id')
        payment_uuid = request.data.get('payment_uuid')
        transaction_id = request.data.get('transaction_id')
        payment_status = request.data.get('status')

        try:
            # 优先使用 payment_id 查找，如果没有则使用 payment_uuid
            if payment_id:
                payment = Payment.objects.get(payment_id=payment_id)
            elif payment_uuid:
                payment = Payment.objects.get(payment_uuid=payment_uuid)
            else:
                return Response({
                    'success': False,
                    'error': '缺少支付ID'
                }, status=http_status.HTTP_400_BAD_REQUEST)

            # 更新支付状态
            if transaction_id:
                payment.transaction_id = transaction_id
            if payment_status is not None:
                payment.status = payment_status
            if payment_status == 1:  # 支付成功
                payment.paid_at = timezone.now()
            payment.save()

            if payment_status == 1:  # 支付成功
                # 更新订单状态（内部接口）
                try:
                    service_client.patch('OrderService', f'/api/orders/internal/orders/{payment.order_uuid}/', {
                        'status': 1,
                        'payment_time': timezone.now().isoformat()
                    })
                except Exception as e:
                    logger.warning(f"更新订单状态失败: {e}")

                # 发送支付成功通知
                try:
                    service_client.post('NotificationService', '/api/internal/notifications/create/', {
                        'user_uuid': str(payment.user_uuid),
                        'title': '支付成功',
                        'content': f'订单 {payment.order_uuid} 支付成功，金额 ¥{payment.amount}',
                        'type': 'payment',
                        'related_id': str(payment.order_uuid),
                        'related_data': {
                            'payment_id': payment.payment_id,
                            'amount': str(payment.amount)
                        }
                    })
                except Exception as e:
                    logger.warning(f"发送支付成功通知失败: {e}")

            return Response({'success': True, 'message': '回调处理成功'})

        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'error': '支付记录不存在'
            }, status=http_status.HTTP_404_NOT_FOUND)


class PaymentQueryByOrderAPIView(GenericAPIView, MicroserviceBaseView):
    """通过订单ID查询支付记录"""
    # permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=http_status.HTTP_401_UNAUTHORIZED)

        # 根据订单ID查询支付记录
        payments = Payment.objects.filter(
            order_uuid=order_id,
            user_uuid=user_uuid
        ).order_by('-created_at')

        serializer = PaymentSerializer(payments, many=True)
        return Response({
            'code': '200',
            'message': 'success',
            'data': serializer.data
        })


class PaymentRecordsAPIView(PaymentListAPIView):
    """支付记录列表 - 兼容性别名"""
    pass


class PaymentCancelAPIView(GenericAPIView, MicroserviceBaseView):
    """取消支付"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, payment_id):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=http_status.HTTP_401_UNAUTHORIZED)

        payment = get_object_or_404(
            Payment,
            payment_uuid=payment_id,
            user_uuid=user_uuid
        )

        # 只有待支付的订单才能取消
        if payment.status != 0:
            return Response({
                'error': '只有待支付的订单才能取消'
            }, status=http_status.HTTP_400_BAD_REQUEST)

        payment.status = 4  # 已取消
        payment.save()

        return Response({
            'message': '支付已取消',
            'payment_id': payment.payment_id
        })


class PaymentRefundAPIView(GenericAPIView, MicroserviceBaseView):
    """支付退款"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=http_status.HTTP_401_UNAUTHORIZED)

        # 根据订单UUID查找对应的支付记录
        try:
            payment = Payment.objects.get(
                order_uuid=order_id,
                user_uuid=user_uuid,
                status=2  # 只查找支付成功的记录
            )
        except Payment.DoesNotExist:
            return Response({
                'error': '未找到对应的支付成功记录'
            }, status=http_status.HTTP_404_NOT_FOUND)

        refund_amount = request.data.get('refund_amount', payment.amount)
        refund_reason = request.data.get('refund_reason', '用户申请退款')

    # 调用第三方支付接口进行退款（模拟）
        refund_result = self._process_refund(payment, refund_amount, refund_reason)

        if refund_result.get('success'):
            # 更新支付状态
            payment.status = 3  # 已退款
            payment.save()

            # 发送退款成功通知
            try:
                service_client.post('NotificationService', '/api/internal/notifications/create/', {
                    'user_uuid': str(user_uuid),
                    'title': '退款成功',
                    'content': f'订单 {payment.order_uuid} 退款成功，金额 ¥{refund_amount}',
                    'type': 'refund',
                    'related_id': str(payment.order_uuid),
                    'related_data': {
                        'payment_id': payment.payment_id,
                        'refund_amount': str(refund_amount)
                    }
                })
            except Exception as e:
                logger.warning(f"发送退款通知失败: {e}")

            return Response({
                'message': '退款申请提交成功',
                'refund_id': refund_result.get('refund_id')
            })
        else:
            return Response({
                'error': '退款处理失败',
                'details': refund_result.get('error', '未知错误')
            }, status=http_status.HTTP_400_BAD_REQUEST)

    def _process_refund(self, payment, refund_amount, refund_reason):
        """处理退款逻辑"""
        # TODO: 实现具体的退款处理逻辑
        # 这里应该调用支付宝、微信支付等第三方退款接口

        # 模拟退款处理
        return {
            'success': True,
            'refund_id': f"refund_{uuid.uuid4().hex[:16]}"
        }


class PaymentStatsAPIView(GenericAPIView, MicroserviceBaseView):
    """支付统计"""
    # permission_classes = [IsAuthenticated]

    def get(self, request):
    # 从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=http_status.HTTP_401_UNAUTHORIZED)

        payments = Payment.objects.filter(user_uuid=user_uuid)

        from django.db.models import Sum
        stats = {
            'total_payments': payments.count(),
            'successful_payments': payments.filter(status=1).count(),
            'failed_payments': payments.filter(status=2).count(),
            'refunded_payments': payments.filter(status=3).count(),
            'total_amount': payments.filter(status=1).aggregate(Sum('amount'))['amount__sum'] or 0,
        }

        # 最近30天支付统计
        from datetime import datetime, timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_payments = payments.filter(created_at__gte=thirty_days_ago, status=1)

        stats['recent_payments'] = recent_payments.count()
        stats['recent_amount'] = recent_payments.aggregate(Sum('amount'))['amount__sum'] or 0

        return Response(stats)
