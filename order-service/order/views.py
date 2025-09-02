"""
订单服务视图 - 微服务版本
使用Spring Cloud Gateway解析的用户UUID，避免调用UserService
"""
import logging
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveAPIView,
    GenericAPIView
)
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, Q
from .models import Order, OrderItem

# 添加公共模块路径 - 必须在导入 serializers 之前
import sys
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 检测环境：容器环境 vs 本地开发环境
if BASE_DIR.startswith('/app'):
    # Docker 容器环境：/app/order/views.py -> BASE_DIR=/app -> PARENT_DIR=/app
    PARENT_DIR = BASE_DIR
else:
    # 本地开发环境：D:\CFMP-order\order-service\order\views.py -> BASE_DIR=D:\CFMP-order\order-service -> PARENT_DIR=D:\CFMP-order
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

# 现在可以安全地导入依赖 common 模块的 serializers
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer
)
from common.service_client import service_client
from common.microservice_base import MicroserviceBaseView
import uuid
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderListCreateAPIView(ListCreateAPIView, MicroserviceBaseView):
    """订单列表和创建"""
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination
   # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的订单"""
    # 微服务通信：从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Order.objects.none()

        status_filter = getattr(self.request, 'query_params', {}).get('status')
        queryset = Order.objects.filter(buyer_uuid=user_uuid).prefetch_related('order_items')

        if status_filter and status_filter != 'all':
            status_map = {
                'pending_payment': 0,
                'paid': 1,
                'completed': 2,
                'cancelled': 3
            }
            if status_filter in status_map:
                queryset = queryset.filter(status=status_map[status_filter])

        # 排序
        sort = getattr(self.request, 'query_params', {}).get('sort', 'created_desc')
        if sort == 'created_desc':
            queryset = queryset.order_by('-created_at')
        elif sort == 'created_asc':
            queryset = queryset.order_by('created_at')
        elif sort == 'amount_desc':
            queryset = queryset.order_by('-total_amount')
        elif sort == 'amount_asc':
            queryset = queryset.order_by('total_amount')

        return queryset

    def list(self, request, *args, **kwargs):
        """返回订单列表 - 兼容原有API响应格式"""
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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """创建订单

        微服务通信点：
        1. 调用ProductService验证商品信息和库存
        2. 创建订单后调用NotificationService发送通知
        """
    # 微服务通信：从Spring Cloud Gateway获取用户UUID
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(
            data=request.data,
            context={'buyer_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)

    # TODO(订单冲突检查 - 暂缓实现)：
    # 需求：避免同一买家在未支付状态下重复创建“包含相同商品”的订单（旧 root 行为）。
    # 建议实现（后续再做）：
    # - 按 buyer_uuid + status=0（待支付） 检索订单，判断是否已包含本次请求中的 product_uuid。
    # - 若存在冲突，直接返回 400（避免重复创建）。
    # 说明：当前仅加注释，不改变逻辑，以免影响现有流程。

        # 在创建订单前，调用ProductService验证商品存在与库存（兼容旧API路径）
        for item in serializer.validated_data.get('items', []):
            pid = item.get('product_uuid')
            qty = int(item.get('quantity', 1) or 1)
            product_data = None
            try:
                product_data = service_client.get('ProductService', f'/api/products/{pid}/')
                if not product_data:
                    product_data = service_client.get('ProductService', f'/api/product/{pid}/')
            except Exception:
                product_data = None
            if not product_data:
                return Response({'error': f'商品不存在: {pid}'}, status=status.HTTP_400_BAD_REQUEST)
            if (product_data.get('stock') is not None) and (int(product_data.get('stock')) < qty):
                return Response({'error': f'商品库存不足: {pid}'}, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.save()

        # 创建订单后发送通知（内部接口）
        try:
            service_client.post('NotificationService', '/api/internal/notifications/create/', {
                'user_uuid': str(user_uuid),
                'title': '订单创建成功',
                'content': f'您的订单 {order.order_id} 已创建成功，等待支付',
                'type': 'transaction',
                'related_id': str(order.order_id),
                'related_data': {
                    'total_amount': str(order.total_amount)
                }
            })
        except Exception as e:
            logger.warning(f"发送订单创建通知失败: {e}")

        response_serializer = OrderDetailSerializer(order)
        return Response({
            'code': '200',
            'message': '订单创建成功',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class OrderDetailAPIView(RetrieveUpdateDestroyAPIView, MicroserviceBaseView):
    """订单详情、更新、删除"""
    queryset = Order.objects.all()
    serializer_class = OrderDetailSerializer
    # permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        """只能访问自己的订单"""
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Order.objects.none()
        return Order.objects.filter(buyer_uuid=user_uuid).prefetch_related('order_items')

    def retrieve(self, request, *args, **kwargs):
        """获取订单详情 - 兼容原有API响应格式"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'code': '200',
            'message': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """更新订单

        微服务通信点：状态变更时通知其他服务
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_status = instance.status

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_order = serializer.save()

        # 状态变更通知
        if old_status != updated_order.status:
            try:
                status_messages = {0: '等待支付', 1: '已支付', 2: '已完成', 3: '已取消'}
                service_client.post('NotificationService', '/api/internal/notifications/create/', {
                    'user_uuid': str(updated_order.buyer_uuid),
                    'title': '订单状态更新',
                    'content': f'您的订单 {updated_order.order_id} 状态已更新为：{status_messages.get(updated_order.status, "未知")}',
                    'type': 'transaction',
                    'related_id': str(updated_order.order_id),
                    'related_data': {
                        'status': updated_order.status
                    }
                })
            except Exception as e:
                logger.warning(f"发送订单状态变更通知失败: {e}")

        return Response({
            'code': '200',
            'message': '订单更新成功',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """删除订单"""
        instance = self.get_object()

        # 只有未支付的订单才能删除
        if instance.status != 0:
            return Response({
                'error': '只有未支付的订单才能删除'
            }, status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response({
            'code': '200',
            'message': '订单删除成功',
            'data': None
        })


class OrderCancelAPIView(GenericAPIView, MicroserviceBaseView):
    """取消订单"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        # 只有未支付的订单才能取消
        if order.status != 0:
            return Response({
                'error': '只有未支付的订单才能取消'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.status = 3  # 已取消
        order.save()

        # 取消订单通知
        try:
            service_client.post('NotificationService', '/api/internal/notifications/create/', {
                'user_uuid': str(user_uuid),
                'title': '订单已取消',
                'content': f'您的订单 {order.order_id} 已成功取消',
                'type': 'transaction',
                'related_id': str(order.order_id),
                'related_data': {
                    'action': 'cancelled'
                }
            })
        except Exception as e:
            logger.warning(f"发送订单取消通知失败: {e}")

        return Response({'message': '订单已取消'})


class OrderPayAPIView(GenericAPIView, MicroserviceBaseView):
    """订单支付"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        # 只有未支付的订单才能支付
        if order.status != 0:
            return Response({
                'error': '订单状态不允许支付'
            }, status=status.HTTP_400_BAD_REQUEST)

        payment_method = request.data.get('payment_method', 'alipay')

        # 调用PaymentService内部API创建并处理支付
        try:
            payment_result = service_client.post('PaymentService', '/api/payment/create/', {
                'order_uuid': str(order.order_uuid),
                'payment_method': payment_method,
                'amount': str(order.total_amount),
                'payment_subject': f'订单支付 - {order.order_id}'
            })

            if payment_result and payment_result.get('success'):
                # 内部API会处理状态更新和回写，本服务可根据需要更新本地状态
                order.status = 1
                order.payment_time = timezone.now()
                order.save()

                return Response({
                    'message': '支付成功',
                    'order_status': order.status,
                    'payment': payment_result.get('data')
                })
            else:
                return Response({
                    'error': '支付失败',
                    'details': (payment_result or {}).get('error', '未知错误')
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"调用支付服务失败: {e}")
            return Response({
                'error': '支付系统暂时不可用，请稍后重试'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


class OrderCompleteAPIView(GenericAPIView, MicroserviceBaseView):
    """完成订单"""
    # permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        # 只有已支付的订单才能完成
        if order.status != 1:
            return Response({
                'error': '只有已支付的订单才能完成'
            }, status=status.HTTP_400_BAD_REQUEST)

        order.status = 2  # 已完成
        order.save()

        # 完成订单通知
        try:
            service_client.post('NotificationService', '/api/internal/notifications/create/', {
                'user_uuid': str(user_uuid),
                'title': '订单已完成',
                'content': f'您的订单 {order.order_id} 已完成',
                'type': 'transaction',
                'related_id': str(order.order_id),
                'related_data': {
                    'action': 'completed'
                }
            })
        except Exception as e:
            logger.warning(f"发送订单完成通知失败: {e}")

        return Response({'message': '订单已完成'})


class OrderDetailByUUIDAPIView(RetrieveAPIView, MicroserviceBaseView):
    """通过UUID获取订单详情 - 供内部服务调用"""
    serializer_class = OrderDetailSerializer
    # permission_classes = [AllowAny]  # 内部API不需要用户认证
    lookup_field = 'order_uuid'

    def get_queryset(self):
        return Order.objects.all().prefetch_related('order_items')

    def retrieve(self, request, *args, **kwargs):
        """获取订单详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class OrderStatsAPIView(GenericAPIView, MicroserviceBaseView):
    """订单统计"""
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        # 统计用户订单数据
        orders = Order.objects.filter(buyer_uuid=user_uuid)

        stats = {
            'total_orders': orders.count(),
            'pending_payment': orders.filter(status=0).count(),
            'paid_orders': orders.filter(status=1).count(),
            'completed_orders': orders.filter(status=2).count(),
            'cancelled_orders': orders.filter(status=3).count(),
            'total_amount': orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        }

        # 最近30天订单趋势
        from datetime import datetime, timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_orders = orders.filter(created_at__gte=thirty_days_ago)

        stats['recent_orders'] = recent_orders.count()
        stats['recent_amount'] = recent_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        return Response(stats)


class OrderInternalAPIView(GenericAPIView):
    """内部订单API - 供其他微服务调用"""
    # permission_classes = [AllowAny]  # 内部API不需要用户认证

    def get(self, request, order_uuid):
        """获取订单信息 - 供PaymentService等调用"""
        try:
            order = Order.objects.get(order_uuid=order_uuid)
            serializer = OrderDetailSerializer(order)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': '订单不存在'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, order_uuid):
        """更新订单状态 - 供PaymentService调用"""
        try:
            order = Order.objects.get(order_uuid=order_uuid)

            # 只允许更新特定字段
            allowed_fields = ['status', 'payment_time']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}

            serializer = OrderDetailSerializer(order, data=update_data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # 刷新实例，确保后续读取到最新状态
            order.refresh_from_db()

            # 发送状态变更通知（内部接口）
            if 'status' in update_data:
                try:
                    service_client.post('NotificationService', '/api/internal/notifications/create/', {
                        'user_uuid': str(order.buyer_uuid),
                        'title': '订单状态更新',
                        'content': f'您的订单 {order.order_id} 状态已更新',
                        'type': 'transaction',
                        'related_id': str(order.order_id),
                        'related_data': {
                            'status': order.status
                        }
                    })
                except Exception as e:
                    logger.warning(f"发送订单状态变更通知失败: {e}")

            return Response({
                'success': True,
                'data': serializer.data
            })
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': '订单不存在'
            }, status=status.HTTP_404_NOT_FOUND)


# 兼容性视图 - 保持与原有API的兼容性
class OrderListAPIView(ListAPIView, MicroserviceBaseView):
    """订单列表 - 兼容原有API /api/orders/"""
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Order.objects.none()

        return Order.objects.filter(buyer_uuid=user_uuid).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """返回订单列表 - 兼容原有API响应格式"""
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


class OrderSoldListAPIView(ListAPIView, MicroserviceBaseView):
    """返回所有卖家是当前用户的订单"""
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取当前用户作为卖家的所有订单"""
        user_uuid = self.get_user_uuid_from_request()
        if not user_uuid:
            return Order.objects.none()

        # 直接通过seller_uuid查询订单
        return Order.objects.filter(seller_uuid=user_uuid).prefetch_related('order_items').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """返回卖家订单列表 - 兼容原有API响应格式"""
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
