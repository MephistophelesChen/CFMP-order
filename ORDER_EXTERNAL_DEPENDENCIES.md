# Order模块微服务外部依赖分析 (更新版)

## 🎯 **明确的职责边界**

我们负责的**内部微服务** (可自行添加API):
- ✅ **order-service** (订单管理)
- ✅ **payment-service** (支付处理)
- ✅ **notification-service** (通知管理)

**外部微服务** (需要等待或要求实现):
- ⏳ **UserService** (用户管理、认证)
- ⏳ **ProductService** (商品管理、库存)

## 📋 **Order模块外部依赖清单**

### 1. **UserService 依赖**
**调用位置**: order-service/order/views.py
```python
# 用户身份验证
user_data = service_client.post('UserService', '/api/auth/verify-token/', {'token': token})

# 获取用户信息
user_info = service_client.get('UserService', f'/api/users/{user_uuid}/')
```

**需要的API** (CFMP中应该已存在):
- ✅ `POST /api/auth/verify-token/` - JWT验证
- ✅ `GET /api/users/{uuid}/` - 获取用户信息

### 2. **ProductService 依赖**
**调用位置**: common/microservice_base.py + order-service/order/views.py
```python
# 获取商品信息
product_data = service_client.get('ProductService', f'/api/product/{product_uuid}/')

# 恢复库存 (订单取消时)
result = service_client.post('ProductService', f'/api/product/{product_uuid}/restore-stock/', {
    'quantity': quantity
})
```

**需要的API**:
- ✅ `GET /api/product/{product_id}/` - 获取商品详情 (CFMP中已存在)
- ❌ `POST /api/product/{product_id}/restore-stock/` - **恢复库存 (需要ProductService新增)**

## 🔧 **我们已实现的内部API**

### PaymentService 新增API
- ✅ `POST /api/payment/{order_id}/refund/` - 订单退款处理

### OrderService 新增API
- ✅ `GET /api/orders/internal/orders/{order_uuid}/` - 内部订单查询

### NotificationService 优化API
- ✅ `POST /api/internal/notifications/create/` - 内部通知创建 (权限优化)

## 🔄 **完整的订单取消流程**

```python
def cancel_order():
    # 1. 验证用户权限 (本地 + UserService)
    user_uuid = get_user_uuid_from_request()

    # 2. 检查订单状态 (本地)
    order = Order.objects.get(order_id=order_id, buyer_uuid=user_uuid)

    # 3. 处理退款 (调用我们的PaymentService)
    refund_result = service_client.post('PaymentService',
                                       f'/api/payment/{order_id}/refund/', {
                                           'refund_amount': order.total_amount,
                                           'refund_reason': cancel_reason
                                       })

    # 4. 恢复库存 (调用外部ProductService - 需要ProductService实现新API)
    for item in order.items.all():
        service_client.post('ProductService',
                           f'/api/product/{item.product_id}/restore-stock/', {
                               'quantity': item.quantity,
                               'reason': 'order_cancelled',
                               'order_id': order.order_id
                           })

    # 5. 更新订单状态 (本地)
    order.status = 3  # 已取消
    order.cancel_reason = cancel_reason
    order.save()

    # 6. 发送取消通知 (调用我们的NotificationService)
    service_client.post('NotificationService',
                       '/api/internal/notifications/create/', {
                           'user_uuid': user_uuid,
                           'type': 0,
                           'title': '订单取消通知',
                           'content': f'您的订单 {order.order_id} 已成功取消',
                           'related_id': str(order.order_uuid)
                       })
```

## 📈 **对外部服务的API要求**

### ProductService 需要新增的API

#### `POST /api/product/{product_id}/restore-stock/`
```json
{
  "summary": "恢复商品库存",
  "description": "订单取消或退款时恢复商品库存",
  "request_body": {
    "quantity": 2,
    "reason": "order_cancelled",
    "order_id": "CFMP202506080001"
  },
  "response": {
    "code": 200,
    "message": "库存恢复成功",
    "data": {
      "success": true,
      "product_id": 123,
      "current_stock": 15,
      "restored_quantity": 2
    }
  }
}
```

## ✅ **当前状态总结**

### 内部微服务 (我们负责) - 100%完成
- **order-service**: 完整实现，包含内部API
- **payment-service**: 完整实现，包含退款API
- **notification-service**: 完整实现，优化内部调用API

### 外部依赖 (需要其他团队配合)
- **UserService**: 假设已存在，API兼容
- **ProductService**: 需要新增库存恢复API

### API兼容性
- ✅ 对外用户API: 100%兼容原有接口
- ✅ 内部微服务通信: 完整实现
- ⏳ 外部依赖: 等待ProductService新增库存恢复API

我们的Order模块微服务化已经完成，只需要ProductService配合实现库存恢复API即可！
