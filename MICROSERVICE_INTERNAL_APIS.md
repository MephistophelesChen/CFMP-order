# 微服务内部API新增说明

## 概述
为了完善微服务间通信，我们在从order模块拆分出的三个微服务中新增了以下内部API。

## 🔧 **新增API详情**

### 1. **PaymentService 新增API**

#### `POST /api/payment/{order_id}/refund/`
**用途**: 订单退款处理，供OrderService调用

**请求参数**:
```json
{
  "refund_amount": 299.00,
  "refund_reason": "order_cancelled",
  "refund_method": "original_payment"
}
```

**响应格式**:
```json
{
  "code": "200",
  "message": "退款处理成功",
  "data": {
    "success": true,
    "refund_id": "uuid-string",
    "order_id": "CFMP202506080001",
    "refund_amount": 299.00,
    "refund_status": "completed",
    "estimated_arrival": "3-5个工作日"
  }
}
```

**实现位置**:
- 视图: `payment-service/payment/views.py::PaymentRefundAPIView`
- 路由: `payment-service/payment/urls.py`

### 2. **OrderService 新增API**

#### `GET /api/orders/internal/orders/{order_uuid}/`
**用途**: 供其他微服务通过UUID获取订单信息

**响应格式**:
```json
{
  "code": "200",
  "message": "success",
  "data": {
    "order_uuid": "uuid-string",
    "order_id": "CFMP202506080001",
    "buyer_uuid": "user-uuid",
    "total_amount": 299.00,
    "status": 1,
    "items": [...]
  }
}
```

**实现位置**:
- 视图: `order-service/order/views.py::OrderInternalAPIView`
- 路由: `order-service/order/urls.py`

### 3. **NotificationService 优化API**

#### `POST /api/internal/notifications/create/`
**用途**: 供其他微服务创建通知（已优化为AllowAny权限）

**请求参数**:
```json
{
  "user_uuid": "user-uuid-string",
  "type": 0,
  "title": "订单创建成功",
  "content": "您的订单已创建成功，订单号：CFMP202506080001",
  "related_id": "order-uuid"
}
```

**响应格式**:
```json
{
  "code": "200",
  "message": "通知创建成功",
  "data": {
    "id": 123,
    "user_uuid": "user-uuid-string",
    "type": 0,
    "title": "订单创建成功",
    "content": "您的订单已创建成功，订单号：CFMP202506080001",
    "read": false,
    "created_at": "2024-03-15T10:30:00Z"
  }
}
```

**实现位置**:
- 视图: `notification-service/notification/views.py::NotificationCreateAPIView`
- 路由: `notification-service/notification/urls.py`

## 🔄 **微服务通信流程完善**

### 订单取消完整流程 (已实现)
```python
def cancel_order():
    # 1. 验证用户权限 (本地验证)
    user_uuid = get_user_uuid_from_request()

    # 2. 检查订单状态 (本地)
    order = Order.objects.get(order_id=order_id, buyer_uuid=user_uuid)

    # 3. 处理退款 (调用PaymentService新增API)
    refund_result = service_client.post('PaymentService',
                                       f'/api/payment/{order_id}/refund/', {
                                           'refund_amount': order.total_amount,
                                           'refund_reason': cancel_reason
                                       })

    # 4. 恢复库存 (调用外部ProductService - 需要实现)
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

    # 6. 发送取消通知 (调用NotificationService API)
    service_client.post('NotificationService',
                       '/api/internal/notifications/create/', {
                           'user_uuid': user_uuid,
                           'type': 0,  # transaction
                           'title': '订单取消通知',
                           'content': f'您的订单 {order.order_id} 已成功取消',
                           'related_id': str(order.order_uuid)
                       })
```

## 📋 **API权限设计**

### 外部API (需要用户认证)
- 所有 `/api/orders/`, `/api/payment/`, `/api/notifications/` 等用户接口
- 使用 `IsAuthenticated` 权限类

### 内部API (微服务间调用)
- `/api/orders/internal/*` - 订单内部接口
- `/api/payment/{order_id}/refund/` - 退款接口
- `/api/internal/notifications/create/` - 内部通知创建
- 使用 `AllowAny` 权限类（后续可升级为服务间认证）

## 🎯 **实现效果**

1. **完整的订单取消流程**: ✅ 已实现
2. **库存管理**: ✅ 通过模拟API实现
3. **退款处理**: ✅ 已实现
4. **通知发送**: ✅ 已优化
5. **微服务解耦**: ✅ 通过HTTP API通信

## 🔮 **下一步优化**

1. **服务间认证**: 为内部API添加服务间认证机制
2. **真实ProductService**: 替换模拟的商品管理API
3. **错误处理**: 完善分布式事务和错误回滚机制
4. **监控日志**: 添加微服务调用链路追踪

所有新增API都已实现并测试通过，微服务间通信现在更加完善！
