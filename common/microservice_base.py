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
        """从请求中获取用户UUID

        微服务通信点：与UserService通信验证用户身份
        """
        # 方案1：从JWT token中解析用户UUID
        auth_header = self.request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # TODO: 实现JWT解析逻辑或调用UserService验证
            try:
                user_data = service_client.post('UserService', '/api/auth/verify-token/',
                                              {'token': token})
                if user_data and user_data.get('success'):
                    return user_data.get('user_uuid')
            except Exception as e:
                logger.warning(f"调用UserService验证token失败: {e}")

        # 方案2：临时从session或用户对象获取
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            # 假设用户模型有uuid字段，或者使用用户ID作为临时方案
            user_id = getattr(self.request.user, 'pk', None)
            return getattr(self.request.user, 'uuid', None) or str(user_id) if user_id else None

        # 方案3：开发环境下的模拟用户UUID
        logger.warning("无法获取用户UUID，使用默认值进行开发测试")
        return str(uuid.uuid4())  # 临时模拟UUID

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
            # 兼容原有API路径格式
            product_data = service_client.get('ProductService', f'/api/product/{product_uuid}/')
            return product_data
        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None

    def restore_product_stock(self, product_uuid, quantity):
        """恢复商品库存

        微服务通信点：调用ProductService恢复库存
        这是新增的微服务接口，需要ProductService实现
        """
        try:
            result = service_client.post('ProductService', f'/api/product/{product_uuid}/restore-stock/', {
                'quantity': quantity
            })
            return result
        except Exception as e:
            logger.error(f"恢复商品库存失败: {e}")
            return None

    def send_notification(self, user_uuid, notification_type, title, content, related_id=None):
        """发送通知

        微服务通信点：调用NotificationService发送通知
        """
        try:
            result = service_client.post('NotificationService', '/api/notifications/', {
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

    def create_payment(self, order_uuid, user_uuid, amount, payment_method, subject):
        """创建支付订单

        微服务通信点：调用PaymentService创建支付
        """
        try:
            result = service_client.post('PaymentService', '/api/payments/', {
                'order_uuid': order_uuid,
                'user_uuid': user_uuid,
                'amount': amount,
                'payment_method': payment_method,
                'payment_subject': subject
            })
            return result
        except Exception as e:
            logger.error(f"创建支付订单失败: {e}")
            return None

    def update_order_status(self, order_uuid, status, **kwargs):
        """更新订单状态

        微服务通信点：调用OrderService更新订单状态
        """
        try:
            data = {'status': status}
            data.update(kwargs)
            result = service_client.put('OrderService', f'/api/orders/{order_uuid}/', data)
            return result
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            return None


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
        # TODO: 实现服务健康检查
        # 可以通过Nacos或直接调用服务健康检查接口
        return service_name in self.registered_services

    def get_available_services(self):
        """获取所有可用服务"""
        return list(self.registered_services)


# 全局服务注册表实例
service_registry = ServiceRegistry()

# 假设的外部服务状态（实际应从Nacos或服务发现机制获取）
# TODO: 这些服务需要实际注册到系统中
EXTERNAL_SERVICES = {
    'UserService': {'port': 8004, 'status': 'assumed_available'},
    'ProductService': {'port': 8005, 'status': 'assumed_available'},
    'RootService': {'port': 8006, 'status': 'assumed_available'},  # 根服务/管理服务
}
