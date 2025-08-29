"""
微服务通信基类
提供通用的微服务间通信功能
"""
import uuid
import logging
from rest_framework.views import APIView
from common.service_client import service_client

logger = logging.getLogger(__name__)


class MicroserviceBaseView(APIView):
    """微服务视图基类

    提供通用的微服务间通信功能，包括：
    1. 用户身份验证
    2. 服务间调用
    3. 错误处理
    """

    def get_user_uuid_from_request(self):
        """从Spring Cloud Gateway解析的请求头中获取用户UUID

        微服务通信点：从Spring Cloud Gateway添加的HTTP头获取用户身份信息
        """
        # 方案1：从Spring Cloud Gateway添加的HTTP头获取用户UUID
        user_uuid = self.request.META.get('HTTP_X_USER_UUID')
        if user_uuid:
            logger.debug(f"从Spring Cloud Gateway获取到用户UUID: {user_uuid}")
            return user_uuid

        # 方案2：从其他可能的头字段获取
        user_uuid = self.request.META.get('HTTP_X_USER_ID')
        if user_uuid:
            logger.debug(f"从HTTP_X_USER_ID获取到用户UUID: {user_uuid}")
            return user_uuid

    # 方案3：从JWT payload中获取（如果网关解析并注入到头中）
        user_uuid = self.request.META.get('HTTP_X_JWT_USER_UUID')
        if user_uuid:
            logger.debug(f"从JWT payload获取到用户UUID: {user_uuid}")
            return user_uuid

        # 兼容性：仍保留直接从Django用户对象获取的逻辑（开发环境）
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            user_id = getattr(self.request.user, 'pk', None)
            user_uuid = getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None
            if user_uuid:
                logger.debug(f"从Django用户对象获取到用户UUID: {user_uuid}")
                return user_uuid

        logger.warning("无法从任何来源获取用户UUID，这可能表示网关配置有问题")
        return None

    def verify_order_ownership(self, order_uuid, user_uuid):
        """验证订单归属权

        微服务通信点：调用OrderService验证订单归属
        """
        try:
            order_data = service_client.get('OrderService', f'/api/orders/{order_uuid}/')
            if not order_data:
                return False, "订单不存在"

            if order_data.get('buyer_uuid') != user_uuid:
                return False, "订单不属于当前用户"

            return True, order_data
        except Exception as e:
            logger.error(f"验证订单归属权失败: {e}")
            return False, "服务异常"

    def get_product_info(self, product_uuid):
        """获取商品信息

        微服务通信点：调用ProductService获取商品信息
        兼容原有API: GET /api/product/{product_id}/
        """
        try:
            # 兼容 /api/products/{id}/ 与 /api/product/{id}/ 两种风格
            product_data = service_client.get('ProductService', f'/api/products/{product_uuid}/')
            if not product_data:
                product_data = service_client.get('ProductService', f'/api/product/{product_uuid}/')
            return product_data
        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None

    def update_product_stock(self, product_uuid, quantity: int):
        """更新商品库存（支持增加或减少）

        微服务通信点：调用 ProductService 新接口
        POST /api/product/{product_uuid}/update-stock/

        约定：
    - 使用字段 quantity 表示库存变化量，正数为增加，负数为减少
        - 返回体需检查 result.success
        """
        try:
            result = service_client.post(
                'ProductService',
                f'/api/product/{product_uuid}/update-stock/',
                {
                    'quantity': int(quantity)
                }
            )
            if not result or not result.get('success'):
                logger.warning(
                    f"更新商品库存失败: product={product_uuid}, quantity={quantity}, resp={result}"
                )
                return None
            return result
        except Exception as e:
            logger.error(f"更新商品库存调用异常: {e}")
            return None

    def restore_product_stock(self, product_uuid, quantity: int):
        """兼容旧方法：恢复商品库存 -> 走新接口 update-stock（正向 delta）"""
        return self.update_product_stock(product_uuid, quantity=int(quantity))

    def create_payment(self, order_uuid, user_uuid, amount, payment_method, subject):
        """创建支付订单

        微服务通信点：调用PaymentService创建支付
        """
        try:
            # 使用支付服务创建端点（兼容当前实现）
            result = service_client.post('PaymentService', '/api/payment/create/', {
                'order_uuid': str(order_uuid),
                'payment_method': payment_method,
                'amount': str(amount),
                'payment_subject': subject
            })
            return result
        except Exception as e:
            logger.error(f"创建支付订单失败: {e}")
            return None

    def update_order_status(self, order_uuid, status, **kwargs):
        """更新订单状态

        微服务通信点：调用OrderService更新订单状态（内部接口）
        """
        try:
            data = {'status': status}
            data.update(kwargs)
            result = service_client.patch('OrderService', f'/api/orders/internal/orders/{order_uuid}/', data)
            return result
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            return None

    def send_notification(self, user_uuid, notification_type, title, content, related_id=None):
        """发送通知

        微服务通信点：调用NotificationService发送通知
        """
        try:
            # 使用通知服务的内部创建接口
            result = service_client.post('NotificationService', '/api/internal/notifications/create/', {
                'user_uuid': user_uuid,
                'type': notification_type,
                'title': title,
                'content': content,
                'related_id': related_id
            })
            return result
        except Exception as e:
            logger.warning(f"发送通知失败: {e}")
            return None

    # 已移除重复的 create_payment 与 update_order_status 定义，统一走内部接口与当前支付创建端点


class ServiceRegistry:
    """服务注册表

    记录各微服务的注册状态和可用性
    """

    def __init__(self):
        self.registered_services = set()

    def register_service(self, service_name):
        """注册服务"""
        self.registered_services.add(service_name)
        logger.info(f"服务已注册: {service_name}")

    def is_service_available(self, service_name):
        """检查服务是否可用"""
        # 可以通过Nacos或直接调用服务健康检查接口
        return service_name in self.registered_services

    def get_available_services(self):
        """获取所有可用服务"""
        return list(self.registered_services)


# 全局服务注册表实例
service_registry = ServiceRegistry()

# 假设的外部服务状态（实际应从Nacos或服务发现机制获取）
# 这些服务需要实际注册到系统中
EXTERNAL_SERVICES = {
    'UserService': {'port': 8004, 'status': 'assumed_available'},
    'ProductService': {'port': 8005, 'status': 'assumed_available'},
    'RootService': {'port': 8006, 'status': 'assumed_available'},  # 根服务/管理服务
}
