# CFMP-Order 微服务系统

## 项目简介

CFMP-Order 是一个基于 Django 和 Nacos 的微服务架构系统，实现了订单处理、支付管理和通知服务的完整业务流程。系统采用服务发现、自动注册、负载均衡等微服务核心技术。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OrderService  │    │ PaymentService  │    │NotificationSrvc │
│   (订单服务)     │    │   (支付服务)     │    │   (通知服务)     │
│   Port: 8001    │    │   Port: 8002    │    │   Port: 8003    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────┬───────────┴──────────────────────┘
                     │
           ┌─────────▼──────────┐
           │   Nacos Registry   │
           │  (服务注册中心)     │
           │  Port: 8848        │
           └────────────────────┘
```

### 服务模块

1. **OrderService (订单服务)**
   - 端口: 8001
   - 功能: 订单创建、查询、状态管理
   - 数据库: MySQL/SQLite

2. **PaymentService (支付服务)**
   - 端口: 8002
   - 功能: 支付处理、支付状态跟踪
   - 数据库: MySQL/SQLite

3. **NotificationService (通知服务)**
   - 端口: 8003
   - 功能: 消息推送、邮件通知
   - 数据库: MySQL/SQLite

4. **Nacos 服务注册中心**
   - 端口: 8848
   - 功能: 服务发现、配置管理、健康检查

## 技术栈

- **后端框架**: Django 5.2 + Django REST Framework
- **服务发现**: Nacos (阿里巴巴开源)
- **数据库**: MySQL / SQLite
- **容器化**: Docker + Docker Compose
- **编程语言**: Python 3.12+
- **依赖管理**: pip + requirements.txt

## 核心特性

- ✅ **微服务架构**: 服务解耦，独立部署
- ✅ **服务发现**: 基于 Nacos 的自动服务注册与发现
- ✅ **健康检查**: 自动心跳检测和故障转移
- ✅ **配置管理**: 环境变量统一配置
- ✅ **容器化部署**: Docker 一键部署
- ✅ **RESTful API**: 标准的 REST 接口设计
- ✅ **数据库迁移**: Django ORM 自动建表
- ✅ **日志管理**: 结构化日志输出

## 快速开始

### 1. 环境要求

- Python 3.12+
- Docker & Docker Compose
- Git

### 2. 克隆项目

```bash
git clone https://github.com/MephistophelesChen/CFMP-order.git
cd CFMP-order
```

### 3. 环境配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置你的环境参数：
```bash
# Nacos 配置
NACOS_SERVER=127.0.0.1:8848
NACOS_NAMESPACE=

# 数据库配置
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# Django 配置
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# 服务端口配置
ORDER_SERVICE_PORT=8001
PAYMENT_SERVICE_PORT=8002
NOTIFICATION_SERVICE_PORT=8003
```

### 4. 安装依赖

为每个服务安装 Python 依赖：

```bash
# 订单服务
cd order-service
pip install -r requirements.txt
cd ..

# 支付服务
cd payment-service
pip install -r requirements.txt
cd ..

# 通知服务
cd notification-service
pip install -r requirements.txt
cd ..
```

### 5. 数据库迁移

为每个服务执行数据库迁移：

```bash
# 订单服务
cd order-service
python manage.py makemigrations
python manage.py migrate
cd ..

# 支付服务
cd payment-service
python manage.py makemigrations
python manage.py migrate
cd ..

# 通知服务
cd notification-service
python manage.py makemigrations
python manage.py migrate
cd ..
```

### 6. 启动服务

#### 方式一: 使用脚本启动 (推荐)

**Windows:**
```bash
.\start-services.bat
```

**Linux/macOS:**
```bash
chmod +x start-services.sh
./start-services.sh
```

#### 方式二: 手动启动

```bash
# 启动订单服务
cd order-service
python manage.py runserver 8001 &

# 启动支付服务
cd ../payment-service
python manage.py runserver 8002 &

# 启动通知服务
cd ../notification-service
python manage.py runserver 8003 &
```

#### 方式三: Docker 启动

```bash
docker-compose -f docker-compose-services.yml up -d
```

### 7. 验证服务

访问以下 URL 验证服务是否正常运行：

- 订单服务: http://localhost:8001/api/orders/
- 支付服务: http://localhost:8002/api/payments/
- 通知服务: http://localhost:8003/api/notifications/

## API 文档

### 订单服务 API

**基础路径**: `http://localhost:8001/api/orders/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/orders/` | 获取订单列表 |
| POST | `/api/orders/` | 创建新订单 |
| GET | `/api/orders/{id}/` | 获取订单详情 |
| PUT | `/api/orders/{id}/` | 更新订单 |
| DELETE | `/api/orders/{id}/` | 删除订单 |

**示例请求**:
```bash
# 创建订单
curl -X POST http://localhost:8001/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "张三",
    "total_amount": 299.99,
    "status": "pending"
  }'
```

### 支付服务 API

**基础路径**: `http://localhost:8002/api/payments/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/payments/` | 获取支付记录 |
| POST | `/api/payments/` | 创建支付记录 |
| GET | `/api/payments/{id}/` | 获取支付详情 |

### 通知服务 API

**基础路径**: `http://localhost:8003/api/notifications/`

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/notifications/` | 获取通知列表 |
| POST | `/api/notifications/` | 发送通知 |

## 测试

项目包含了完整的测试套件：

### 单元测试

```bash
# 测试订单服务
cd order-service
python manage.py test

# 测试支付服务
cd ../payment-service
python manage.py test

# 测试通知服务
cd ../notification-service
python manage.py test
```

### Nacos 集成测试

```bash
# 测试 Nacos 基础功能
python test_basic_nacos.py

# 测试服务注册
python test_nacos_registration.py
```

### 接口测试

使用 curl 或 Postman 测试 REST API：

```bash
# 健康检查
curl http://localhost:8001/health/
curl http://localhost:8002/health/
curl http://localhost:8003/health/

# 服务发现测试
curl http://localhost:8001/api/orders/discover/payment/
```

## 配置管理

### 环境变量说明

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `NACOS_SERVER` | Nacos 服务器地址 | `127.0.0.1:8848` |
| `NACOS_NAMESPACE` | Nacos 命名空间 | (空) |
| `DEBUG` | Django 调试模式 | `True` |
| `SECRET_KEY` | Django 密钥 | 随机生成 |
| `DB_ENGINE` | 数据库引擎 | `sqlite3` |
| `ALLOWED_HOSTS` | 允许的主机 | `localhost,127.0.0.1` |

### Nacos 配置

Nacos 服务器配置位于 `nacos_heartbeat.py` 中，包含：
- 服务器地址和端口
- 认证信息
- 命名空间配置

## 部署指南

### 本地开发部署

1. 按照"快速开始"章节配置环境
2. 使用 `start-services.bat` 启动所有服务
3. 通过浏览器访问各服务接口

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose -f docker-compose-services.yml up -d

# 查看服务状态
docker-compose -f docker-compose-services.yml ps

# 查看日志
docker-compose -f docker-compose-services.yml logs -f
```

### 生产环境部署

1. **环境变量配置**:
   ```bash
   # 生产环境配置
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   NACOS_SERVER=your-nacos-server:8848
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=cfmp_order
   DB_USER=your-db-user
   DB_PASSWORD=your-db-password
   DB_HOST=your-db-host
   DB_PORT=3306
   ```

2. **数据库配置**:
   - 使用 MySQL 作为生产数据库
   - 配置数据库连接池
   - 设置数据库备份策略

3. **反向代理**:
   - 使用 Nginx 作为反向代理
   - 配置 SSL 证书
   - 设置负载均衡

4. **监控和日志**:
   - 配置日志收集 (ELK Stack)
   - 设置监控告警 (Prometheus + Grafana)
   - 配置健康检查

## 故障排查

### 常见问题

1. **服务无法注册到 Nacos**
   - 检查 Nacos 服务器是否启动
   - 验证网络连接和防火墙设置
   - 查看服务日志中的错误信息

2. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证数据库连接参数
   - 确认数据库用户权限

3. **端口冲突**
   - 使用 `netstat -an` 查看端口占用
   - 修改 `.env` 中的端口配置
   - 重启相关服务

4. **模块导入错误**
   - 检查 Python 路径配置
   - 验证依赖包安装
   - 查看 Django 设置文件

### 日志文件位置

- 订单服务: `order-service/logs/order-service.log`
- 支付服务: `payment-service/logs/payment-service.log`
- 通知服务: `notification-service/logs/notification-service.log`

## 开发指南

### 代码结构

```
CFMP-order/
├── common/                 # 公共模块
│   ├── config.py          # 配置管理
│   ├── nacos_client.py    # Nacos 客户端
│   └── service_registry.py # 服务注册
├── order-service/         # 订单服务
├── payment-service/       # 支付服务
├── notification-service/  # 通知服务
├── .env                   # 环境变量 (不提交)
├── .env.example           # 环境变量模板
├── docker-compose-services.yml # Docker 配置
└── README.md              # 项目文档
```

### 添加新服务

1. 创建新的 Django 项目
2. 配置 `apps.py` 继承服务注册功能
3. 更新 Docker 配置
4. 添加相应的测试

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用 Django 最佳实践
- 服务名称使用 CamelCase (如: OrderService)
- API 路径使用小写和下划线

## 贡献指南

1. Fork 项目到你的 GitHub 账户
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者: MephistophelesChen
- 项目地址: https://github.com/MephistophelesChen/CFMP-order
- 问题反馈: [GitHub Issues](https://github.com/MephistophelesChen/CFMP-order/issues)

## 更新日志

### v1.0.0 (2025-08-28)
- ✅ 初始版本发布
- ✅ 完成三个微服务的基础功能
- ✅ 集成 Nacos 服务发现
- ✅ 支持 Docker 部署
- ✅ 完善的文档和测试

---

感谢使用 CFMP-Order 微服务系统！如有问题请查看文档或提交 Issue。
