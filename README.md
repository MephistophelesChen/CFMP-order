# CFMP订单系统

基于微服务架构的订单管理系统，包含订单、支付、通知三个核心微服务。

## 系统架构

### 核心微服务
- **order-service** (端口: 8001) - 订单管理服务
- **payment-service** (端口: 8002) - 支付处理服务
- **notification-service** (端口: 8003) - 通知管理服务

### 基础设施
- **MySQL** (端口: 3306) - 数据库服务（容器化部署）
- **Redis** (端口: 6379) - 缓存服务

### 外部服务
- **Nacos** (端口: 8848) - 服务注册与发现（外部：123.57.145.79）

## 快速启动

### 1. Docker Compose 部署（推荐）

**完整部署**（包含所有基础设施）：
```bash
# 启动所有服务
docker-compose up -d

# 仅启动微服务（需要外部基础设施）
docker-compose -f docker-compose-services.yml up -d
```

**Windows 批处理脚本**：
```cmd
# 完整启动
start-services.bat

# 仅启动微服务
start-microservices-only.bat

# 停止所有服务
stop-services.bat
```

### 2. Kubernetes 部署

```cmd
cd k8s
deploy.bat       # 部署服务
status.bat       # 查看状态
cleanup.bat      # 清理部署
```

## 服务访问

### Docker 部署
- 订单服务: http://localhost:8001/api/orders/
- 支付服务: http://localhost:8002/api/payments/
- 通知服务: http://localhost:8003/api/notifications/
- MySQL数据库: localhost:3306
- Redis缓存: localhost:6379

### 外部服务
- Nacos控制台: http://123.57.145.79:8848/nacos

### Kubernetes 部署
- 订单服务: http://localhost:30001
- 支付服务: http://localhost:30002
- 通知服务: http://localhost:30003

## 项目结构

```
CFMP-order/
├── common/                      # 公共模块
│   ├── microservice_base.py   # 微服务基类
│   ├── service_client.py      # 服务间通信
│   └── nacos_client.py        # Nacos客户端
├── order-service/              # 订单服务
├── payment-service/            # 支付服务
├── notification-service/       # 通知服务
├── k8s/                       # Kubernetes部署配置
├── sql/                       # 数据库初始化脚本
├── docker-compose.yml         # 完整部署配置
├── docker-compose-services.yml # 仅微服务配置
├── start-services.bat         # Windows启动脚本
└── stop-services.bat          # Windows停止脚本
```

## 开发指南

### 用户认证
所有微服务继承`MicroserviceBaseView`基类，支持多种认证方式：
- HTTP头认证：`X-User-UUID`、`X-User-ID`、`X-JWT-User-UUID`
- JWT Token认证
- 外部服务调用

### API测试
```bash
# 测试订单服务
curl -H "X-User-UUID: test-user-123" \
     http://localhost:8001/api/orders/

# 测试支付服务
curl -H "X-User-UUID: test-user-123" \
     http://localhost:8002/api/payments/
```

## 环境要求

- Docker & Docker Compose
- Python 3.11+
- MySQL 8.0+
- Redis 7+

## 相关文档

- [系统架构文档](SYSTEM_DOCUMENTATION.md)
- [Kubernetes部署指南](k8s/README.md)
- [API迁移说明](APISIX_MIGRATION_SUMMARY.md)
