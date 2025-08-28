"""
订单服务视图 - 微服务版本
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
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
import uuid


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
        # TODO: 从JWT token或session中获取用户UUID
        # user_uuid = self.request.user.id  # 临时使用user.id
        user_uuid = getattr(self.request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        """创建订单"""
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        serializer = self.get_serializer(
            data=request.data,
            context={'buyer_uuid': user_uuid}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # 返回创建的订单详情
        order_serializer = OrderDetailSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)
class OrderDetailAPIView(RetrieveUpdateDestroyAPIView):
    """订单详情"""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'

    def get_queryset(self):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(self.request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟
        return Order.objects.filter(buyer_uuid=user_uuid).prefetch_related('order_items')


class OrderCancelAPIView(GenericAPIView):
    """取消订单"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

        order = get_object_or_404(
            Order,
            order_id=order_id,
            buyer_uuid=user_uuid
        )

        if order.status != 0:  # 只能取消待支付的订单
            return Response(
                {'error': '只能取消待支付的订单'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cancel_reason = request.data.get('cancel_reason', '用户主动取消')
        order.status = 3  # 已取消
        order.cancel_reason = cancel_reason
        order.updated_at = timezone.now()
        order.save()

        return Response({'message': '订单已取消'})


class OrderCompleteAPIView(GenericAPIView):
    """完成订单"""
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

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


class OrderStatsAPIView(GenericAPIView):
    """订单统计"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # TODO: 从JWT token获取用户UUID
        user_uuid = getattr(request.user, 'id', None) or str(uuid.uuid4())  # 临时模拟

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
