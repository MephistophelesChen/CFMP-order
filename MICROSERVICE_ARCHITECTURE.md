# CFMP 订单系统 - 微服务架构改造

## 项目概述

本项目是对原有单体订单系统的微服务化改造，将原来紧耦合的系统拆分为独立的微服务，实现松耦合、高可用的分布式架构。

## 数据库改造

### 旧版问题
- **高耦合**：使用Django外键直接关联User和Product模型
- **单一数据库**：所有数据存储在同一个数据库中，缺乏数据独立性

### 新版改进
- **数据解耦**：使用UUID替代外键，移除跨服务的数据库依赖
- **统一数据库，分表管理**：
  - 数据库名：`cfmp_microservices`
  - 订单表：`order`, `order_item`
  - 支付表：`payment`
  - 通知表：`notification`, `security_policy`, `risk_assessment`

### 数据库配置
```python
# 统一数据库配置，避免资源冗余
DATABASE_CONFIG = {
    'ORDER_DB': {
        'NAME': 'cfmp_microservices',  # 统一数据库
        # ... 其他配置
    },
    'PAYMENT_DB': {
        'NAME': 'cfmp_microservices',  # 同一数据库
        # ... 其他配置
    },
    'NOTIFICATION_DB': {
        'NAME': 'cfmp_microservices',  # 同一数据库
        # ... 其他配置
    }
}
```

## 微服务架构

### 已实现的微服务

#### 1. OrderService (端口: 8001)
- **功能**：订单管理、订单状态跟踪
- **模型**：Order, OrderItem
- **关键改造**：
  - 使用 `buyer_uuid` 替代 User 外键
  - 使用 `product_uuid` 替代 Product 外键
  - 添加商品快照信息（冗余设计）

#### 2. PaymentService (端口: 8002)
- **功能**：支付处理、支付记录管理
- **模型**：Payment
- **关键改造**：
  - 使用 `order_uuid` 和 `user_uuid` 替代外键
  - 添加支付回调处理

#### 3. NotificationService (端口: 8003)
- **功能**：通知管理、安全策略、风险评估
- **模型**：Notification, SecurityPolicy, RiskAssessment
- **关键改造**：
  - 使用 `user_uuid` 替代 User 外键
  - 提供通知创建API供其他服务调用

### 假设存在的外部微服务

#### 4. UserService (端口: 8004)
- **功能**：用户管理、认证授权
- **状态**：需要注册到系统中
- **通信接口**：
  - `POST /api/auth/verify-token/` - JWT验证
  - `GET /api/users/{uuid}/` - 获取用户信息

#### 5. ProductService (端口: 8005)
- **功能**：商品管理、库存管理
- **状态**：需要注册到系统中
- **通信接口**：
  - `GET /api/products/{uuid}/` - 获取商品信息
  - `POST /api/products/{uuid}/restore-stock/` - 恢复库存

#### 6. RootService (端口: 8006)
- **功能**：系统管理、配置管理、监控
- **状态**：需要注册到系统中

## 微服务间通信

### 通信机制
1. **服务发现**：使用Nacos进行服务注册与发现
2. **HTTP通信**：使用 `common.service_client` 进行REST API调用
3. **认证方式**：JWT Token 或 服务间认证

### 关键通信点

#### OrderService 通信点
```python
# 创建订单时的微服务通信流程
def create_order():
    # 1. 验证用户身份 (UserService)
    user_data = service_client.post('UserService', '/api/auth/verify-token/', {'token': token})

    # 2. 验证商品信息 (ProductService)
    product_data = service_client.get('ProductService', f'/api/products/{product_uuid}/')

    # 3. 创建订单 (本地)
    order = Order.objects.create(...)

    # 4. 发送通知 (NotificationService)
    service_client.post('NotificationService', '/api/notifications/', {...})
```

#### PaymentService 通信点
```python
# 创建支付时的微服务通信流程
def create_payment():
    # 1. 验证订单状态 (OrderService)
    order_data = service_client.get('OrderService', f'/api/orders/{order_uuid}/')

    # 2. 创建支付记录 (本地)
    payment = Payment.objects.create(...)

    # 3. 发送支付通知 (NotificationService)
    service_client.post('NotificationService', '/api/notifications/', {...})
```

#### NotificationService 通信点
```python
# 创建通知时的用户验证
def create_notification():
    # 1. 验证用户存在 (UserService)
    user_data = service_client.get('UserService', f'/api/users/{user_uuid}/')

    # 2. 创建通知 (本地)
    notification = Notification.objects.create(...)

    # 3. 实时推送 (可选)
    # self._send_real_time_notification(notification)
```

### 订单取消的完整流程
```python
def cancel_order():
    # 1. 验证用户权限 (本地 + UserService)
    # 2. 检查订单状态 (本地)
    # 3. 处理退款 (PaymentService)
    # 4. 恢复库存 (ProductService)
    # 5. 更新订单状态 (本地)
    # 6. 发送取消通知 (NotificationService)
```

## TODO 清单

### 高优先级
1. **实现JWT认证**：完善UserService的token验证机制
2. **服务注册**：将UserService、ProductService、RootService注册到Nacos
3. **健康检查**：实现服务健康检查机制
4. **错误处理**：完善微服务调用的错误处理和熔断机制

### 中优先级
1. **数据迁移**：从旧版单体系统迁移数据到新微服务
2. **监控告警**：实现服务监控和告警机制
3. **性能优化**：优化微服务间调用性能
4. **日志聚合**：实现分布式日志收集和分析

### 低优先级
1. **服务间认证**：实现更安全的服务间认证机制
2. **配置中心**：使用Nacos配置中心管理配置
3. **链路追踪**：实现分布式链路追踪
4. **容器化部署**：Docker容器化部署

## 部署说明

### 启动顺序
1. **基础设施**：MySQL、Nacos
2. **核心服务**：UserService（如果已实现）
3. **业务服务**：OrderService、PaymentService、NotificationService
4. **外部服务**：ProductService、RootService

### 环境变量
```bash
# 数据库配置
CFMP_DB_NAME=cfmp_microservices
CFMP_DB_USER=root
CFMP_DB_PASSWORD=123456
CFMP_DB_HOST=127.0.0.1
CFMP_DB_PORT=3306

# Nacos配置
NACOS_SERVER=127.0.0.1:8848
NACOS_NAMESPACE=cfmp-microservices
NACOS_USERNAME=nacos
NACOS_PASSWORD=nacos
```

### 启动命令
```bash
# 启动订单服务
cd order-service && python manage.py runserver 8001

# 启动支付服务
cd payment-service && python manage.py runserver 8002

# 启动通知服务
cd notification-service && python manage.py runserver 8003
```

## 总结

本次改造成功将单体订单系统拆分为微服务架构，主要成果：

1. **数据解耦**：移除了跨服务的数据库外键依赖
2. **服务拆分**：按业务领域拆分为独立的微服务
3. **通信机制**：建立了完整的微服务间HTTP通信框架
4. **可扩展性**：为后续功能扩展奠定了良好基础

系统现在具备了微服务的基本特征：
- ✅ 服务独立部署
- ✅ 数据隔离
- ✅ 技术栈独立
- ✅ 失败隔离
- ⏳ 服务发现（部分实现）
- ⏳ 配置管理（部分实现）
