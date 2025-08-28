# 交易模块微服务路由配置总结

## 概述
交易模块已完成微服务化拆分，所有API路径与原有系统完全兼容，前端无需任何修改。

## 微服务部署端口
- **订单服务**: localhost:8002
- **支付服务**: localhost:8003
- **通知服务**: localhost:8004

## API路由映射详情

### 1. 订单管理服务 (order-service:8002)

```
原有路径                          微服务路径                        服务端口
POST   /api/orders/               → POST   /api/orders/               :8002
GET    /api/orders/               → GET    /api/orders/               :8002
GET    /api/orders/{order_id}/    → GET    /api/orders/{order_id}/    :8002
PUT    /api/orders/{order_id}/cancel/    → PUT    /api/orders/{order_id}/cancel/    :8002
PUT    /api/orders/{order_id}/complete/  → PUT    /api/orders/{order_id}/complete/  :8002
GET    /api/orders/stats/         → GET    /api/orders/stats/         :8002
```

**URL配置文件**:
- `order-service/config/urls.py`: `path('api/orders/', include('order.urls'))`
- `order-service/order/urls.py`: 具体端点定义

### 2. 支付服务 (payment-service:8003)

```
原有路径                               微服务路径                              服务端口
POST   /api/payment/create/            → POST   /api/payment/create/             :8003
GET    /api/payment/callback/{method}/ → GET    /api/payment/callback/{method}/  :8003
POST   /api/payment/callback/{method}/ → POST   /api/payment/callback/{method}/  :8003
GET    /api/payment/{order_id}/        → GET    /api/payment/{order_id}/         :8003
GET    /api/payment/records/           → GET    /api/payment/records/            :8003
POST   /api/payment/{payment_id}/cancel/ → POST   /api/payment/{payment_id}/cancel/ :8003
```

**URL配置文件**:
- `payment-service/config/urls.py`: `path('api/payment/', include('payment.urls'))`
- `payment-service/payment/urls.py`: 具体端点定义

### 3. 通知服务 (notification-service:8004)

```
原有路径                                    微服务路径                                   服务端口
GET    /api/notifications/                  → GET    /api/notifications/                   :8004
GET    /api/notifications/{id}/             → GET    /api/notifications/{id}/              :8004
DELETE /api/notifications/{id}/             → DELETE /api/notifications/{id}/              :8004
PUT    /api/notifications/{id}/read/        → PUT    /api/notifications/{id}/read/         :8004
PUT    /api/notifications/read-all/         → PUT    /api/notifications/read-all/          :8004
GET    /api/notifications/unread-count/     → GET    /api/notifications/unread-count/      :8004
```

**URL配置文件**:
- `notification-service/config/urls.py`: `path('api/', include('notification.urls'))`
- `notification-service/notification/urls.py`: 包含notifications和security路由

### 4. 安全策略服务 (notification-service:8004)

```
原有路径                                  微服务路径                                服务端口
POST   /api/security/risk-assessment/     → POST   /api/security/risk-assessment/      :8004
POST   /api/security/fraud-detection/     → POST   /api/security/fraud-detection/      :8004
GET    /api/security/policies/            → GET    /api/security/policies/             :8004
PUT    /api/security/policies/            → PUT    /api/security/policies/             :8004
```

## 负载均衡器配置示例

### Nginx配置
```nginx
# 订单管理
location /api/orders/ {
    proxy_pass http://localhost:8002/api/orders/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# 支付服务
location /api/payment/ {
    proxy_pass http://localhost:8003/api/payment/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# 通知服务
location /api/notifications/ {
    proxy_pass http://localhost:8004/api/notifications/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# 安全策略
location /api/security/ {
    proxy_pass http://localhost:8004/api/security/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### API Gateway配置 (Kong/Zuul等)
```yaml
routes:
  - name: order-service
    paths: ["/api/orders"]
    service:
      url: "http://localhost:8002"

  - name: payment-service
    paths: ["/api/payment"]
    service:
      url: "http://localhost:8003"

  - name: notification-service
    paths: ["/api/notifications", "/api/security"]
    service:
      url: "http://localhost:8004"
```

## 前端集成说明

### ✅ 无需修改的内容
1. **API路径**: 所有路径保持完全一致
2. **请求参数**: 参数名称和格式不变
3. **响应格式**: 统一的 `{code, message, data}` 格式
4. **认证方式**: 继续使用JWT Bearer Token
5. **分页参数**: page, page_size等参数不变

### 📝 推荐的部署方案
1. **方案一**: 使用负载均衡器(推荐)
   - 前端继续调用原有API路径
   - 负载均衡器根据路径路由到对应微服务
   - 对前端完全透明

2. **方案二**: 修改前端配置
   - 只需修改API base URL配置
   - 不同功能模块指向不同服务端口
   - 业务逻辑代码无需修改

## 微服务内部通信

### 内部API端点 (不对外暴露)
```
# 订单服务内部API
GET /api/orders/internal/{order_uuid}/

# 通知服务内部API
POST /api/internal/notifications/create/
```

### 服务间通信示例
```python
# 订单服务调用支付服务
payment_result = service_client.post('PaymentService', '/api/payment/create/', {
    'order_id': order.order_id,
    'amount': order.total_amount
})

# 支付服务调用通知服务
notification_result = service_client.post('NotificationService', '/api/internal/notifications/create/', {
    'user_uuid': user_uuid,
    'title': '支付成功',
    'content': f'订单{order_id}支付成功'
})
```

## 测试验证

### 运行完整兼容性测试
```bash
python test_order_api_compatibility.py
```

### 单独测试各服务
```bash
# 测试订单服务
curl http://localhost:8002/api/orders/

# 测试支付服务
curl http://localhost:8003/api/payment/records/

# 测试通知服务
curl http://localhost:8004/api/notifications/
```

## 总结

✅ **完全兼容**: 所有原有API路径、参数、响应格式100%兼容
✅ **零修改**: 前端代码无需任何修改
✅ **透明切换**: 通过负载均衡器实现无感知切换
✅ **向后兼容**: 保持原有所有功能特性

微服务拆分成功完成，前端可以无缝迁移到新架构！
