"""
订单服务视图 - 微服务版本
"""
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
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, CreateOrderSerializer
)
from common.service_client import service_client
import uuid
import logging

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """标准分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderListCreateAPIView(ListCreateAPIView):
    """订单列表和创建"""
    serializer_class = OrderListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的订单"""
        # 微服务通信：从认证头或JWT中获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
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

    def _get_user_uuid_from_request(self):
        """从请求中获取用户UUID

        微服务通信点：这里需要与UserService通信验证用户身份
        """
        # 方案1：从JWT token中解析用户UUID
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: 实现JWT解析逻辑或调用UserService验证
            # user_data = service_client.post('UserService', '/api/auth/verify-token/',
            #                               {'token': token})
            # return user_data.get('user_uuid') if user_data else None
            pass

        # 方案2：临时从session或用户对象获取
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # 假设用户模型有uuid字段，或者使用用户ID作为临时方案
            user_id = getattr(self.request.user, 'pk', None)
            return getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None

        # 方案3：开发环境下的模拟用户UUID
        logger.warning("无法获取用户UUID，使用默认值进行开发测试")
        return str(uuid.uuid4())  # 临时模拟UUID

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
        # 微服务通信：获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(
            data=request.data,
            context={'buyer_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)

        # TODO: 在创建订单前，调用ProductService验证商品信息
        # for item in serializer.validated_data.get('items', []):
        #     product_data = service_client.get('ProductService',
        #                                     f'/api/products/{item["product_uuid"]}/')
        #     if not product_data:
        #         return Response({'error': f'商品不存在: {item["product_uuid"]}'},
        #                       status=status.HTTP_400_BAD_REQUEST)
        #     if product_data.get('stock', 0) < item.get('quantity', 1):
        #         return Response({'error': f'商品库存不足: {product_data.get("name", "")}'},
        #                       status=status.HTTP_400_BAD_REQUEST)

        order = serializer.save()

        # TODO: 调用NotificationService发送订单创建通知
        # try:
        #     service_client.post('NotificationService', '/api/notifications/', {
        #         'user_uuid': user_uuid,
        #         'type': 0,  # transaction
        #         'title': '订单创建成功',
        #         'content': f'您的订单 {order.order_uuid} 已创建成功，金额：¥{order.total_amount}',
        #         'related_id': str(order.order_uuid)
        #     })
        # except Exception as e:
        #     logger.warning(f"发送订单创建通知失败: {e}")

        # 返回创建的订单详情 - 兼容原有API响应格式
        order_serializer = OrderDetailSerializer(order)
        return Response({
            'code': '200',
            'message': 'success',
            'data': order_serializer.data
        }, status=status.HTTP_201_CREATED)
class OrderDetailAPIView(RetrieveUpdateDestroyAPIView):
    """订单详情

    微服务通信点：
    1. 验证用户权限：确保用户只能访问自己的订单
    2. 更新订单状态时：调用PaymentService或NotificationService
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        """只能访问自己的订单"""
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Order.objects.none()
        return Order.objects.filter(buyer_uuid=user_uuid).prefetch_related('order_items')

    def _get_user_uuid_from_request(self):
        """从请求中获取用户UUID（复用方法）"""
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
        order = serializer.save()

        # 如果状态发生变化，发送通知
        if order.status != old_status:
            # TODO: 调用NotificationService发送状态变更通知
            # try:
            #     status_map = {0: '待支付', 1: '已支付', 2: '已完成', 3: '已取消'}
            #     service_client.post('NotificationService', '/api/notifications/', {
            #         'user_uuid': order.buyer_uuid,
            #         'type': 0,  # transaction
            #         'title': '订单状态变更',
            #         'content': f'您的订单 {order.order_uuid} 状态已更新为：{status_map.get(order.status, "未知")}',
            #         'related_id': str(order.order_uuid)
            #     })
            # except Exception as e:
            #     logger.warning(f"发送订单状态变更通知失败: {e}")
            pass

        # 返回兼容原有API格式的响应
        return Response({
            'code': '200',
            'message': 'success',
            'data': serializer.data
        })


class OrderCancelAPIView(GenericAPIView):
    """取消订单

    微服务通信点：
    1. 调用PaymentService取消支付或退款
    2. 调用ProductService恢复库存
    3. 调用NotificationService发送取消通知
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # 微服务通信：获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        if order.status not in [0, 1]:  # 只能取消待支付或已支付的订单
            return Response(
                {'error': '订单状态不允许取消'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancel_reason = request.data.get('cancel_reason', '用户主动取消')

        # TODO: 如果订单已支付，调用PaymentService进行退款
        # if order.status == 1:  # 已支付
        #     try:
        #         refund_result = service_client.post('PaymentService', '/api/payments/refund/', {
        #             'order_uuid': str(order.order_uuid),
        #             'amount': float(order.total_amount),
        #             'reason': cancel_reason
        #         })
        #         if not refund_result or not refund_result.get('success'):
        #             return Response({'error': '退款处理失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        #     except Exception as e:
        #         logger.error(f"调用退款服务失败: {e}")
        #         return Response({'error': '退款服务异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # TODO: 调用ProductService恢复库存
        # for item in order.order_items.all():
        #     try:
        #         service_client.post('ProductService', f'/api/products/{item.product_uuid}/restore-stock/', {
        #             'quantity': item.quantity
        #         })
        #     except Exception as e:
        #         logger.warning(f"恢复商品库存失败: {e}")

        # 更新订单状态
        order.status = 3  # 已取消
        order.cancel_reason = cancel_reason
        order.updated_at = timezone.now()
        order.save()

        # TODO: 调用NotificationService发送取消通知
        # try:
        #     service_client.post('NotificationService', '/api/notifications/', {
        #         'user_uuid': user_uuid,
        #         'type': 0,  # transaction
        #         'title': '订单已取消',
        #         'content': f'您的订单 {order.order_uuid} 已取消，原因：{cancel_reason}',
        #         'related_id': str(order.order_uuid)
        #     })
        # except Exception as e:
        #     logger.warning(f"发送订单取消通知失败: {e}")

        # 返回兼容原有API格式的响应
        return Response({
            'code': '200',
            'message': '订单已取消',
            'data': None
        })

    def _get_user_uuid_from_request(self):
        """获取用户UUID（复用方法）"""
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


class OrderCompleteAPIView(GenericAPIView):
    """完成订单"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # 微服务通信：获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        if order.status != 1:  # 只能完成已支付的订单
            return Response(
                {'error': '只能完成已支付的订单'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 2  # 已完成
        order.updated_at = timezone.now()
        order.save()

        return Response({'message': '订单已完成'})

    def _get_user_uuid_from_request(self):
        """获取用户UUID（复用方法）"""
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


class OrderStatsAPIView(GenericAPIView):
    """订单统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 微服务通信：获取用户UUID
        user_uuid = self._get_user_uuid_from_request()
        if not user_uuid:
            return Response({'error': '用户身份验证失败'}, status=status.HTTP_401_UNAUTHORIZED)

        orders = Order.objects.filter(buyer_uuid=user_uuid)

        stats = {
            'total_orders': orders.count(),
            'pending_payment': orders.filter(status=0).count(),
            'paid': orders.filter(status=1).count(),
            'completed': orders.filter(status=2).count(),
            'cancelled': orders.filter(status=3).count(),
            'total_amount': orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
        }

        return Response(stats)

    def _get_user_uuid_from_request(self):
        """获取用户UUID（复用方法）"""
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


class AdminOrderListAPIView(ListAPIView):
    """管理员订单列表（兼容原有API /root/order/）

    支持多种查询方式：用户ID、手机号、订单ID、商品ID
    """
    serializer_class = OrderDetailSerializer
    pagination_class = StandardPagination
    # TODO: 改为管理员权限验证
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """根据查询参数筛选订单"""
        queryset = Order.objects.all().prefetch_related('order_items')

        # 支持原有API的查询参数
        buyer_id = getattr(self.request, 'query_params', {}).get('buyer_id')
        phone = getattr(self.request, 'query_params', {}).get('phone')
        order_id = getattr(self.request, 'query_params', {}).get('order_id')
        product_id = getattr(self.request, 'query_params', {}).get('product_id')

        if buyer_id:
            # TODO: 调用UserService根据用户ID获取用户UUID
            # user_data = service_client.get('UserService', f'/api/users/{buyer_id}/')
            # if user_data:
            #     queryset = queryset.filter(buyer_uuid=user_data.get('uuid'))
            queryset = queryset.filter(buyer_uuid=buyer_id)  # 临时直接使用ID

        if phone:
            # TODO: 调用UserService根据手机号获取用户UUID
            # user_data = service_client.get('UserService', f'/api/users/by-phone/{phone}/')
            # if user_data:
            #     queryset = queryset.filter(buyer_uuid=user_data.get('uuid'))
            pass

        if order_id:
            queryset = queryset.filter(order_id=order_id)

        if product_id:
            # 通过订单项查找包含指定商品的订单
            queryset = queryset.filter(order_items__product_uuid=product_id)

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

    def _get_user_uuid_from_request(self):
        """从请求中获取用户UUID

        微服务通信点：这里需要与UserService通信验证用户身份
        """
        # 方案1：从JWT token中解析用户UUID
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: 实现JWT解析逻辑或调用UserService验证
            # user_data = service_client.post('UserService', '/api/auth/verify-token/',
            #                               {'token': token})
            # return user_data.get('user_uuid') if user_data else None
            pass

        # 方案2：临时从session或用户对象获取
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # 假设用户模型有uuid字段，或者使用用户ID作为临时方案
            user_id = getattr(self.request.user, 'pk', None)
            return getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None

        # 方案3：开发环境下的模拟用户UUID
        logger.warning("无法获取用户UUID，使用默认值进行开发测试")
        return str(uuid.uuid4())  # 临时模拟UUID


class OrderDetailByUUIDAPIView(RetrieveAPIView):
    """通过UUID查询订单详情（供其他微服务调用）"""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]  # TODO: 改为服务间认证
    lookup_field = 'order_uuid'

    def get_queryset(self):
        return Order.objects.all().prefetch_related('order_items')

    def retrieve(self, request, *args, **kwargs):
        """返回订单详情"""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Order.DoesNotExist:
            return Response({
                'success': False,
                'error': '订单不存在'
            }, status=status.HTTP_404_NOT_FOUND)


# TODO: 添加与原有API兼容的其他视图
# 1. 订单支付功能 - 需要与PaymentService集成
# 2. 订单物流跟踪 - 可能需要物流服务
# 3. 订单评价功能 - 需要与商品评价系统集成


class OrderInternalAPIView(GenericAPIView):
    """订单内部API - 供其他微服务调用"""
    permission_classes = [AllowAny]  # 内部微服务调用

    def get(self, request, order_uuid):
        """通过UUID获取订单信息 - 供PaymentService等调用"""
        try:
            order = Order.objects.get(order_uuid=order_uuid)
            serializer = OrderDetailSerializer(order)
            return Response({
                'code': '200',
                'message': 'success',
                'data': serializer.data
            })
        except Order.DoesNotExist:
            return Response({
                'code': '404',
                'message': '订单不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)
