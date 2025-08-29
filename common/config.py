"""
微服务公共配置
"""
import os

# 服务配置
SERVICES = {
    # 内部微服务（已实现）
    'ORDER_SERVICE': {
        'name': 'OrderService',
        'port': 8001,
        'version': '1.0.0',
        'status': 'implemented'
    },
    'PAYMENT_SERVICE': {
        'name': 'PaymentService',
        'port': 8002,
        'version': '1.0.0',
        'status': 'implemented'
    },
    'NOTIFICATION_SERVICE': {
        'name': 'NotificationService',
        'port': 8003,
        'version': '1.0.0',
        'status': 'implemented'
    },
    # 外部微服务（假设存在，需要注册）
    'USER_SERVICE': {
        'name': 'UserService',
        'port': 8004,
        'version': '1.0.0',
        'status': 'external_assumed',
        'description': '用户服务 - 管理用户信息、认证授权'
    },
    'PRODUCT_SERVICE': {
        'name': 'ProductService',
        'port': 8005,
        'version': '1.0.0',
        'status': 'external_assumed',
        'description': '商品服务 - 管理商品信息、库存管理'
    },
    'ROOT_SERVICE': {
        'name': 'RootService',
        'port': 8006,
        'version': '1.0.0',
        'status': 'external_assumed',
        'description': '根服务 - 系统管理、配置管理、监控'
    }
}

# Nacos配置 - 外部服务
NACOS_CONFIG = {
    'server_addresses': os.getenv('NACOS_SERVER', '123.57.145.79:8848'),
    'namespace': os.getenv('NACOS_NAMESPACE', 'public'),
    'group': os.getenv('NACOS_GROUP', 'DEFAULT_GROUP'),
    'username': os.getenv('NACOS_USERNAME', 'nacos'),
    'password': os.getenv('NACOS_PASSWORD', 'nacos')
}

# 数据库配置 - 容器化MySQL
DATABASE_CONFIG = {
    'ORDER_DB': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('ORDER_DB_NAME', 'cfmp_order'),
        'USER': os.getenv('ORDER_DB_USER', 'root'),
        'PASSWORD': os.getenv('ORDER_DB_PASSWORD', 'root123'),
        'HOST': os.getenv('ORDER_DB_HOST', 'mysql'),  # Docker容器名
        'PORT': os.getenv('ORDER_DB_PORT', '3306'),
    },
    'PAYMENT_DB': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('PAYMENT_DB_NAME', 'cfmp_payment'),
        'USER': os.getenv('PAYMENT_DB_USER', 'root'),
        'PASSWORD': os.getenv('PAYMENT_DB_PASSWORD', 'root123'),
        'HOST': os.getenv('PAYMENT_DB_HOST', 'mysql'),  # Docker容器名
        'PORT': os.getenv('PAYMENT_DB_PORT', '3306'),
    },
    'NOTIFICATION_DB': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('NOTIFICATION_DB_NAME', 'cfmp_notification'),
        'USER': os.getenv('NOTIFICATION_DB_USER', 'root'),
        'PASSWORD': os.getenv('NOTIFICATION_DB_PASSWORD', 'root123'),
        'HOST': os.getenv('NOTIFICATION_DB_HOST', 'mysql'),  # Docker容器名
        'PORT': os.getenv('NOTIFICATION_DB_PORT', '3306'),
    }
}

# 通用常量
ORDER_STATUS_CHOICES = (
    (0, 'pending_payment'),  # 待支付
    (1, 'paid'),           # 已支付
    (2, 'completed'),      # 已完成
    (3, 'cancelled'),      # 已取消
)

PAYMENT_METHOD_CHOICES = (
    (0, 'alipay'),       # 支付宝支付
    (1, 'wechat_pay'),   # 微信支付
)

PAYMENT_STATUS_CHOICES = (
    (0, 'pending'),      # 待支付
    (1, 'processing'),   # 处理中
    (2, 'success'),      # 成功
    (3, 'failed'),       # 失败
    (4, 'cancelled'),    # 已取消
)

NOTIFICATION_TYPE_CHOICES = (
    (0, 'transaction'),  # 交易通知
    (1, 'system'),       # 系统通知
    (2, 'promotion'),    # 促销通知
)
