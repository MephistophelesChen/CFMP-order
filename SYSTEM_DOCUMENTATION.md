# CFMP订单系统 - 微服务架构文档

## 项目概述

CFMP订单系统是一个基于微服务架构的订单管理系统，包含订单、支付、通知三个核心微服务，使用Apisix作为API网关。

## 系统架构

### 核心微服务
- **order-service** (端口: 8001) - 订单管理服务
- **payment-service** (端口: 8002) - 支付处理服务
- **notification-service** (端口: 8004) - 通知管理服务

### 基础设施
- **Apisix网关** (端口: 9080) - API网关和用户认证
- **Nacos** (端口: 8848) - 服务注册与发现
- **MySQL** (端口: 3306) - 数据库服务

### 外部依赖
- **UserService** - 用户管理与认证（外部）
- **ProductService** - 商品管理与库存（外部）

## 用户认证架构

### Apisix网关认证流程
1. 客户端发送JWT token到Apisix网关
2. 网关验证JWT token并解析用户UUID
3. 网关在HTTP头中添加用户信息：
   - `X-User-UUID`: 主要用户UUID字段
   - `X-User-ID`: 备用用户ID字段
   - `X-JWT-User-UUID`: JWT payload用户UUID
4. 下游微服务从HTTP头获取用户信息

### 微服务用户认证
所有微服务继承`MicroserviceBaseView`基类，通过`get_user_uuid_from_request()`方法获取用户UUID：

```python
user_uuid = self.get_user_uuid_from_request()
if not user_uuid:
    return Response({'error': '用户身份验证失败'}, status=401)
```

## API路由规则

### 网关路由配置
- `/api/orders/*` → order-service:8001
- `/api/payments/*` → payment-service:8002
- `/api/notifications/*` → notification-service:8004
- `/api/security/*` → notification-service:8004

### 主要API端点

#### 订单服务 (order-service)
- `GET /api/orders/` - 获取订单列表
- `POST /api/orders/` - 创建订单
- `GET /api/orders/{order_id}/` - 获取订单详情
- `PUT /api/orders/{order_id}/` - 更新订单
- `DELETE /api/orders/{order_id}/` - 删除订单
- `POST /api/orders/{order_id}/cancel/` - 取消订单
- `POST /api/orders/{order_id}/pay/` - 订单支付
- `GET /api/orders/stats/` - 订单统计

#### 支付服务 (payment-service)
- `GET /api/payments/` - 获取支付记录列表
- `POST /api/payments/` - 创建支付
- `GET /api/payments/{payment_id}/` - 获取支付详情
- `POST /api/payments/{payment_id}/refund/` - 申请退款
- `POST /api/payments/callback/` - 支付回调处理
- `GET /api/payments/stats/` - 支付统计

#### 通知服务 (notification-service)
- `GET /api/notifications/` - 获取通知列表
- `POST /api/notifications/` - 创建通知（内部API）
- `GET /api/notifications/{notification_id}/` - 获取通知详情
- `DELETE /api/notifications/{notification_id}/` - 删除通知
- `POST /api/notifications/{notification_id}/read/` - 标记已读
- `POST /api/notifications/mark-all-read/` - 标记全部已读
- `GET /api/notifications/unread-count/` - 获取未读数量

#### 安全服务 (notification-service)
- `POST /api/security/risk-assessment/` - 风险评估
- `POST /api/security/fraud-detection/` - 欺诈检测

## 微服务通信

### 内部API调用
微服务间通过`service_client`进行HTTP通信：

```python
from common.service_client import service_client

# 调用其他微服务
result = service_client.post('PaymentService', '/api/payments/', payment_data)
```

### 服务注册与发现
- 使用Nacos进行服务注册与发现
- 支持动态端口配置，自动检测可用端口
- 服务启动后自动注册到Nacos

## 数据模型

### 订单服务模型
- `Order` - 订单主表
- `OrderItem` - 订单项目

### 支付服务模型
- `Payment` - 支付记录

### 通知服务模型
- `Notification` - 通知信息
- `SecurityPolicy` - 安全策略
- `RiskAssessment` - 风险评估

## 部署配置

### Docker Compose
使用`docker-compose.yml`进行容器化部署：

```bash
# 启动所有服务
docker-compose up -d

# 启动指定服务
docker-compose up -d order-service payment-service
```

### 环境变量
- `DJANGO_SETTINGS_MODULE` - Django配置模块
- `DEBUG` - 调试模式
- `NACOS_SERVER` - Nacos服务地址
- `*_DB_*` - 数据库连接配置

### 动态端口配置
支持通过以下方式配置端口：
1. 环境变量：`SERVICE_PORT` 或 `ACTUAL_SERVICE_PORT`
2. 命令行参数：`python manage.py runserver 8001`
3. 自动分配：从默认端口开始查找可用端口

## 开发指南

### 项目结构
```
CFMP-order/
├── common/                 # 公共模块
│   ├── microservice_base.py
│   ├── service_client.py
│   └── nacos_client.py
├── order-service/          # 订单服务
├── payment-service/        # 支付服务
├── notification-service/   # 通知服务
├── apisix/                # 网关配置
└── docker-compose.yml     # 容器编排
```

### 开发流程
1. 继承`MicroserviceBaseView`基类
2. 使用`get_user_uuid_from_request()`获取用户信息
3. 通过`service_client`调用其他微服务
4. 遵循RESTful API设计规范

### 测试验证
```bash
# 测试网关认证
curl -H "Authorization: Bearer <jwt-token>" \
     http://localhost:9080/api/orders/

# 测试微服务间通信
curl -X POST http://localhost:8001/api/orders/ \
     -H "Content-Type: application/json" \
     -d '{"items": [...]}'
```

## 最佳实践

### 错误处理
- 统一的错误响应格式
- 适当的HTTP状态码
- 详细的错误日志记录

### 性能优化
- 使用分页查询
- 合理的数据库索引
- 缓存常用数据

### 安全考虑
- JWT token验证
- 用户权限控制
- API访问频率限制
- 敏感数据加密

## 监控和运维

### 日志管理
- 统一的日志格式
- 分级日志记录
- 日志轮转配置

### 健康检查
- 服务健康状态监控
- 数据库连接检查
- 依赖服务可用性检查

### 服务治理
- 熔断器模式
- 重试机制
- 超时控制

## 故障排除

### 常见问题
1. **端口冲突**: 使用动态端口配置
2. **服务发现失败**: 检查Nacos连接状态
3. **用户认证失败**: 验证JWT token和网关配置
4. **微服务通信失败**: 检查服务注册状态

### 调试工具
- Docker容器日志：`docker logs <container-name>`
- Nacos控制台：http://123.57.145.79:8848/nacos/
- 网关管理：http://localhost:9091
