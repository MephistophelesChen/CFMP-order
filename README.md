# CFMP订单系统

## 项目简介

CFMP订单系统是一个基于微服务架构的现代化订单管理系统，使用Apisix网关、Django微服务和Nacos服务发现构建。

## 快速开始

### 环境要求
- Docker & Docker Compose
- Python 3.8+
- MySQL 8.0+

### 启动服务

```bash
# 克隆项目
git clone <repository-url>
cd CFMP-order

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 访问地址
- API网关: http://localhost:9080
- Nacos控制台: http://localhost:8848/nacos
- 订单服务: http://localhost:8001
- 支付服务: http://localhost:8002
- 通知服务: http://localhost:8004

## 系统架构

```
                    ┌─────────────────┐
                    │   Apisix网关     │
                    │   Port: 9080    │
                    └─────────┬───────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌─────────▼───────┐    ┌───────▼──────┐
│ OrderService │    │ PaymentService  │    │NotificationSvc│
│  Port: 8001  │    │   Port: 8002    │    │  Port: 8004  │
└──────────────┘    └─────────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────▼───────┐
                    │  Nacos注册中心   │
                    │   Port: 8848    │
                    └─────────────────┘
```

## 核心特性

### 🚀 微服务架构
- 独立部署的订单、支付、通知服务
- 基于Apisix的API网关
- Nacos服务注册与发现

### 🔒 统一认证
- JWT token验证
- 网关层用户认证
- 用户信息自动注入

### 📈 高可用性
- 动态端口配置
- 健康检查机制
- 服务自动注册

### 🛡️ 安全管理
- 风险评估系统
- 欺诈检测功能
- 安全策略配置

## API文档

### 主要API端点

#### 订单管理
- `GET /api/orders/` - 订单列表
- `POST /api/orders/` - 创建订单
- `GET /api/orders/{id}/` - 订单详情

#### 支付处理
- `GET /api/payments/` - 支付记录
- `POST /api/payments/` - 创建支付
- `POST /api/payments/{id}/refund/` - 申请退款

#### 通知管理
- `GET /api/notifications/` - 通知列表
- `POST /api/notifications/{id}/read/` - 标记已读
- `GET /api/notifications/unread-count/` - 未读数量

## 开发指南

### 项目结构
```
CFMP-order/
├── common/                 # 公共模块
├── order-service/          # 订单服务
├── payment-service/        # 支付服务
├── notification-service/   # 通知服务
├── apisix/                # 网关配置
└── docker-compose.yml     # 容器编排
```

### 开发环境
```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 启动开发服务器
python manage.py runserver 8001
```

## 配置说明

### 环境变量
- `NACOS_SERVER` - Nacos服务地址
- `DJANGO_SETTINGS_MODULE` - Django配置模块
- `*_DB_*` - 数据库连接配置

### JWT配置
在`apisix/apisix.yaml`中配置JWT密钥：
```yaml
jwt-auth:
  secret: "your-jwt-secret"
```

## 文档资源

- 📖 [系统完整文档](./SYSTEM_DOCUMENTATION.md)
- 🔧 [网关配置指南](./apisix/README.md)
- 📝 [迁移总结](./APISIX_MIGRATION_SUMMARY.md)

## 许可证

MIT License
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
