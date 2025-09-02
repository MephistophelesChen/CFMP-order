# CFMP 微服务系统 API 接口文档

## 概述
CFMP (Commerce and Financial Management Platform) 微服务系统包含三个核心服务：
- **Order Service** (订单服务) - 端口: 30001
- **Payment Service** (支付服务) - 端口: 30002
- **Notification Service** (通知服务) - 端口: 30003

## 外部依赖服务
系统依赖以下外部服务：
- **UserService** (用户服务) - 用户信息管理
- **ProductService** (商品服务) - 商品信息管理

---

# 1. Order Service (订单服务)

## 1.1 订单管理接口

### GET /api/orders/
**获取订单列表**

**请求参数:**
```
Query Parameters:
- status: string (可选) - 订单状态过滤 ["pending_payment", "paid", "completed", "cancelled", "all"]
- sort: string (可选) - 排序方式 ["created_desc", "created_asc", "amount_desc", "amount_asc"]
- page: int (可选) - 页码，默认1
- page_size: int (可选) - 每页大小，默认10，最大100
```

**响应体:**
```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "order_id": 123,
            "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "buyer_id": "user123",
            "buyer_uuid": "550e8400-e29b-41d4-a716-446655440001",
            "seller_id": "seller456",
            "seller_uuid": "550e8400-e29b-41d4-a716-446655440002",
            "status": 0,
            "created_at": "2025-01-01T12:00:00Z",
            "payment_method": 0,
            "cancel_reason": null,
            "payment_time": null,
            "remark": "备注信息",
            "shipping_address": "配送地址",
            "shipping_name": "收货人",
            "shipping_phone": "13800138000",
            "shipping_postal_code": "100000",
            "total_amount": "199.98",
            "updated_at": "2025-01-01T12:00:00Z",
            "products": [
                {
                    "product_id": "product123",
                    "product_uuid": "550e8400-e29b-41d4-a716-446655440003",
                    "product_name": "商品名称",
                    "price": "99.99",
                    "quantity": 2,
                    "product_image": "https://example.com/image.jpg"
                }
            ]
        }
    ]
}
```

**微服务调用详情:**

1. **调用 UserService 获取买家信息**
   ```
   GET /api/v1/user/{buyer_uuid}/
   Headers: 无需特殊认证头（内部调用）
   ```
   **预期响应:**
   ```json
   {
       "user_id": "user123",
       "id": "user123",
       "username": "买家用户名",
       "email": "buyer@example.com",
       "phone": "13800138000"
   }
   ```

2. **调用 UserService 获取卖家信息**
   ```
   GET /api/v1/user/{seller_uuid}/
   Headers: 无需特殊认证头（内部调用）
   ```
   **预期响应:**
   ```json
   {
       "user_id": "seller456",
       "id": "seller456",
       "username": "卖家用户名",
       "email": "seller@example.com",
       "phone": "13900139000"
   }
   ```

**调用失败处理:**
- 如果 UserService 调用失败，将返回 UUID 字符串作为 fallback
- 不会影响订单列表的正常返回

---

### POST /api/orders/
**创建订单**

**请求体:**
```json
{
    "products": [
        {
            "product_uuid": "028a38c7-506e-4e13-9c84-2a7ba4165aae",
            "price": 585.85,
            "quantity": 11
        }
    ],
    "seller_uuid": "ea58d0f3-a0ce-4694-950c-5049762024de",
    "shipping_address": "乜桥796号",
    "shipping_name": "卫国栋",
    "shipping_phone": "09391710383",
    "shipping_postal_code": "100000",
    "payment_method": 1,
    "remark": "备注信息"
}
```

**响应体:**
```json
{
    "code": "200",
    "message": "订单创建成功",
    "data": {
        "order_id": 123,
        "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
        // ... 完整订单信息
    }
}
```

**微服务调用详情:**

1. **调用 ProductService 获取商品信息**
   ```
   GET /api/products/{product_uuid}/
   Headers: 无需特殊认证头（内部调用）
   ```
   **预期响应:**
   ```json
   {
       "product_uuid": "028a38c7-506e-4e13-9c84-2a7ba4165aae",
       "name": "商品名称",
       "title": "商品标题",
       "price": 585.85,
       "stock": 100,
       "image": "https://example.com/product.jpg",
       "thumbnail": "https://example.com/thumb.jpg",
       "description": "商品描述"
   }
   ```

   **备用调用 (如果第一个失败):**
   ```
   GET /api/product/{product_uuid}/
   ```

2. **调用 NotificationService 发送订单创建通知**
   ```
   POST /api/internal/notifications/create/
   Headers: Content-Type: application/json
   ```
   **请求体:**
   ```json
   {
       "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
       "title": "订单创建成功",
       "content": "您的订单 123 已创建成功，等待支付",
       "type": "transaction",
       "related_id": "123",
       "related_data": {
           "total_amount": "199.98"
       }
   }
   ```
   **预期响应:**
   ```json
   {
       "code": "200",
       "message": "通知创建成功",
       "data": {
           "id": 789,
           "notification_uuid": "550e8400-e29b-41d4-a716-446655440005",
           "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
           "type": 0,
           "title": "订单创建成功",
           "content": "您的订单 123 已创建成功，等待支付",
           "is_read": false,
           "created_at": "2025-01-01T12:00:00Z"
       }
   }
   ```

**调用失败处理:**
- ProductService 调用失败时，商品名称将显示为 "商品"，图片为空
- NotificationService 调用失败时，只记录警告日志，不影响订单创建

---

### GET /api/orders/sold/
**获取卖家订单列表**

获取当前用户作为卖家的所有订单。

**响应体:** 同订单列表格式

---

### GET /api/orders/{order_id}/
**获取订单详情**

**路径参数:**
- order_id: string - 订单ID

**响应体:**
```json
{
    "code": "200",
    "message": "success",
    "data": {
        // 完整订单详情，包含解密后的配送地址信息
    }
}
```

---

### PUT /api/orders/{order_id}/
**更新订单**

**请求体:**
```json
{
    "status": 1,
    "remark": "更新备注"
}
```

**微服务调用详情:**

**调用 NotificationService 发送状态变更通知**
```
POST /api/internal/notifications/create/
Headers: Content-Type: application/json
```
**请求体:**
```json
{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单状态更新",
    "content": "您的订单 123 状态已更新为：已支付",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "status": 1
    }
}
```
**预期响应:**
```json
{
    "code": "200",
    "message": "通知创建成功",
    "data": {
        "id": 790,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440006",
        "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "type": 0,
        "title": "订单状态更新",
        "content": "您的订单 123 状态已更新为：已支付",
        "is_read": false,
        "created_at": "2025-01-01T12:05:00Z"
    }
}
```

---

### PUT /api/orders/{order_id}/cancel/
**取消订单**

只有待支付状态(status=0)的订单可以取消。

**响应体:**
```json
{
    "message": "订单已取消"
}
```

**微服务调用详情:**

**调用 NotificationService 发送取消通知**
```
POST /api/internal/notifications/create/
Headers: Content-Type: application/json
```
**请求体:**
```json
{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单取消通知",
    "content": "您的订单 123 已成功取消",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "status": 3,
        "cancel_reason": "用户主动取消"
    }
}
```
**预期响应:**
```json
{
    "code": "200",
    "message": "通知创建成功",
    "data": {
        "id": 791,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440007",
        "user_uuid": "550e8400-e29b-41d4-a716-446655440002",
        "type": 0,
        "title": "订单状态更新",
        "content": "您的订单 456 状态已更新为：已取消",
        "is_read": false,
        "created_at": "2025-01-01T12:15:00Z"
    }
}
```

---

### PUT /api/orders/{order_id}/complete/
**完成订单**

只有已支付状态(status=1)的订单可以完成。

**微服务调用详情:**

**调用 NotificationService 发送完成通知**
```
POST /api/internal/notifications/create/
Headers: Content-Type: application/json
```
**请求体:**
```json
{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单完成通知",
    "content": "您的订单 123 已完成",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "status": 2
    }
}
```
**预期响应:**
```json
{
    "code": "200",
    "message": "通知创建成功",
    "data": {
        "id": 792,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440008",
        "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "type": 0,
        "title": "订单完成通知",
        "content": "您的订单 123 已完成",
        "is_read": false,
        "created_at": "2025-01-01T12:20:00Z"
    }
}
```

---

### GET /api/orders/stats/
**订单统计**

**响应体:**
```json
{
    "total_orders": 50,
    "pending_payment": 5,
    "paid_orders": 20,
    "completed_orders": 20,
    "cancelled_orders": 5,
    "total_amount": 10000.00,
    "recent_orders": 10,
    "recent_amount": 2000.00
}
```

---

## 1.2 内部微服务接口

### GET /api/orders/internal/{order_uuid}/
**通过UUID获取订单详情 (内部接口)**

供其他微服务调用，无需用户认证。

**响应体:**
```json
{
    "success": true,
    "data": {
        // 完整订单信息
    }
}
```

---

### GET /api/orders/internal/orders/{order_uuid}/
**内部订单查询接口**

### PATCH /api/orders/internal/orders/{order_uuid}/
**内部订单状态更新接口**

**请求体:**
```json
{
    "status": 1,
    "payment_time": "2025-01-01T12:00:00Z"
}
```

**微服务调用详情:**

**调用 NotificationService 发送状态变更通知**
```
POST /api/internal/notifications/create/
Headers: Content-Type: application/json
```
**请求体:**
```json
{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单状态更新",
    "content": "您的订单 123 状态已更新",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "status": 1
    }
}
```
**预期响应:**
```json
{
    "code": "200",
    "message": "通知创建成功",
    "data": {
        "id": 793,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440009",
        "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "type": 0,
        "title": "订单状态更新",
        "content": "您的订单 123 状态已更新",
        "is_read": false,
        "created_at": "2025-01-01T12:25:00Z"
    }
}
```

---

# 2. Payment Service (支付服务)

## 2.1 支付接口

### POST /api/payment/create/
**创建支付**

**请求体:**
```json
{
    "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "payment_method": "alipay",
    "amount": "199.98",
    "payment_subject": "订单支付 - 123"
}
```

**响应体:**
```json
{
    "success": true,
    "data": {
        "payment_id": 456,
        "payment_uuid": "550e8400-e29b-41d4-a716-446655440004",
        "payment_url": "https://payment.example.com/pay/...",
        "qr_code": "data:image/png;base64,...",
        "expires_at": "2025-01-01T13:00:00Z"
    }
}
```

**微服务调用详情:**

1. **调用 OrderService 验证订单信息**
   ```
   GET /api/orders/internal/{order_uuid}/
   Headers: 无需特殊认证头（内部调用）
   ```
   **预期响应:**
   ```json
   {
       "success": true,
       "data": {
           "order_id": 123,
           "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
           "buyer_uuid": "550e8400-e29b-41d4-a716-446655440001",
           "seller_uuid": "550e8400-e29b-41d4-a716-446655440002",
           "total_amount": "199.98",
           "status": 0,
           "created_at": "2025-01-01T12:00:00Z"
       }
   }
   ```

2. **支付成功后调用 OrderService 更新订单状态**
   ```
   PATCH /api/orders/internal/orders/{order_uuid}/
   Headers: Content-Type: application/json
   ```
   **请求体:**
   ```json
   {
       "status": 1,
       "payment_time": "2025-01-01T12:05:00Z"
   }
   ```
   **预期响应:**
   ```json
   {
       "success": true,
       "data": {
           "order_id": 123,
           "status": 1,
           "payment_time": "2025-01-01T12:05:00Z"
       }
   }
   ```

**调用失败处理:**
- 如果订单验证失败，支付创建将被拒绝
- 如果状态更新失败，会记录错误日志但不影响支付流程

---

### GET /api/payment/callback/{payment_method}/
### POST /api/payment/callback/{payment_method}/
**支付回调接口**

接收支付平台的回调通知。

**路径参数:**
- payment_method: string - 支付方式 ["alipay", "wechat_pay"]

---

### GET /api/payment/records/
**获取支付记录**

**Query Parameters:**
```
- status: string (可选) - 支付状态过滤
- page: int (可选) - 页码
- page_size: int (可选) - 每页大小
```

**响应体:**
```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "payment_id": 456,
            "payment_uuid": "550e8400-e29b-41d4-a716-446655440004",
            "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
            "amount": "199.98",
            "payment_method": 0,
            "status": 2,
            "created_at": "2025-01-01T12:00:00Z",
            "paid_at": "2025-01-01T12:05:00Z",
            "payment_subject": "订单支付 - 123"
        }
    ]
}
```

---

### GET /api/payment/{order_uuid}/
**根据订单UUID查询支付记录**

---

### POST /api/payment/{payment_id}/cancel/
**取消支付**

---

### POST /api/payment/{order_uuid}/refund/
**订单退款**

**请求体:**
```json
{
    "refund_amount": "199.98",
    "refund_reason": "退款原因"
}
```

---

# 3. Notification Service (通知服务)

## 3.1 通知管理接口

### GET /api/notifications/
**获取通知列表**

**Query Parameters:**
```
- type: string (可选) - 通知类型过滤 ["transaction", "system", "promotion"]
- is_read: boolean (可选) - 已读状态过滤
- page: int (可选) - 页码
- page_size: int (可选) - 每页大小
```

**响应体:**
```json
{
    "code": "200",
    "message": "success",
    "data": [
        {
            "id": 789,
            "notification_uuid": "550e8400-e29b-41d4-a716-446655440005",
            "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
            "type": 0,
            "title": "订单创建成功",
            "content": "您的订单 123 已创建成功，等待支付",
            "is_read": false,
            "created_at": "2025-01-01T12:00:00Z",
            "read_at": null,
            "related_id": "123",
            "related_data": {"status": 0}
        }
    ]
}
```

---

### GET /api/notifications/{notification_id}/
**获取通知详情**

### DELETE /api/notifications/{notification_id}/
**删除通知**

---

### PUT /api/notifications/{notification_id}/read/
**标记通知为已读**

**响应体:**
```json
{
    "message": "通知已标记为已读"
}
```

---

### PUT /api/notifications/read-all/
**标记所有通知为已读**

**响应体:**
```json
{
    "message": "所有通知已标记为已读"
}
```

---

### GET /api/notifications/unread-count/
**获取未读通知数量**

**响应体:**
```json
{
    "unread_count": 5
}
```

---

## 3.2 内部微服务接口

### POST /api/internal/notifications/create/
**创建通知 (内部接口)**

供其他微服务调用，无需用户认证。

**请求体:**
```json
{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单状态更新",
    "content": "您的订单 123 状态已更新",
    "type": "transaction",
    "related_id": "123",
    "related_data": {"status": 1}
}
```

**响应体:**
```json
{
    "success": true,
    "data": {
        "id": 789,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440005"
    }
}
```

---

# 4. 微服务间调用关系图

```
OrderService ←→ UserService (获取用户信息)
    ↓
OrderService ←→ ProductService (获取商品信息)
    ↓
OrderService → NotificationService (发送通知)
    ↓
OrderService ←→ PaymentService (支付处理)
    ↓
PaymentService → OrderService (更新订单状态)
    ↓
PaymentService → NotificationService (支付通知)
```

---

# 5. 状态码说明

## 订单状态 (Order Status)
- 0: pending_payment (待支付)
- 1: paid (已支付)
- 2: completed (已完成)
- 3: cancelled (已取消)

## 支付方式 (Payment Method)
- 0: alipay (支付宝)
- 1: wechat_pay (微信支付)

## 支付状态 (Payment Status)
- 0: pending (待支付)
- 1: processing (处理中)
- 2: success (成功)
- 3: failed (失败)
- 4: cancelled (已取消)

## 通知类型 (Notification Type)
- 0: transaction (交易通知) - 用于订单、支付相关通知
- 1: system (系统通知) - 用于系统维护、升级通知
- 2: promotion (促销通知) - 用于营销活动通知

**注意:** 代码中使用 `"transaction"` 来发送订单相关通知，而不是 `"order"`

---

# 8. 详细微服务调用说明

## 8.1 OrderService 发起的调用

### 调用 UserService - 获取用户信息
**场景:** 在序列化订单数据时获取用户友好的ID和信息

**调用接口:**
```
GET /api/v1/user/{user_uuid}/
```

**请求示例:**
```http
GET /api/v1/user/550e8400-e29b-41d4-a716-446655440001/
Content-Type: application/json
```

**成功响应:**
```json
{
    "user_id": "user123",
    "id": "user123",
    "username": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "avatar": "https://example.com/avatar.jpg"
}
```

**失败响应:**
```json
{
    "error": "User not found",
    "code": 404
}
```

**错误处理:** 如果调用失败，返回 UUID 字符串作为 fallback

---

### 调用 ProductService - 获取商品信息
**场景:** 创建订单时获取商品详细信息

**主要调用接口:**
```
GET /api/products/{product_uuid}/
```

**备用调用接口:**
```
GET /api/product/{product_uuid}/
```

**请求示例:**
```http
GET /api/products/028a38c7-506e-4e13-9c84-2a7ba4165aae/
Content-Type: application/json
```

**成功响应:**
```json
{
    "product_uuid": "028a38c7-506e-4e13-9c84-2a7ba4165aae",
    "name": "Apple iPhone 15 Pro",
    "title": "苹果 iPhone 15 Pro 手机",
    "price": 8999.00,
    "stock": 50,
    "image": "https://example.com/iphone15pro.jpg",
    "thumbnail": "https://example.com/iphone15pro_thumb.jpg",
    "description": "最新款 iPhone 15 Pro",
    "category": "手机数码",
    "seller_uuid": "ea58d0f3-a0ce-4694-950c-5049762024de"
}
```

**失败响应:**
```json
{
    "error": "Product not found",
    "code": 404
}
```

**错误处理:** 如果调用失败，商品名称显示为 "商品"，图片为空

---

### 调用 NotificationService - 发送通知
**场景:** 订单状态变更时发送用户通知

**调用接口:**
```
POST /api/internal/notifications/create/
```

**订单创建通知请求:**
```http
POST /api/internal/notifications/create/
Content-Type: application/json

{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单创建成功",
    "content": "您的订单 123 已创建成功，等待支付",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "total_amount": "199.98",
        "status": 0
    }
}
```

**订单状态更新通知请求:**
```http
POST /api/internal/notifications/create/
Content-Type: application/json

{
    "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "title": "订单状态更新",
    "content": "您的订单 123 状态已更新为：已支付",
    "type": "transaction",
    "related_id": "123",
    "related_data": {
        "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "old_status": 0,
        "new_status": 1
    }
}
```

**成功响应:**
```json
{
    "code": "200",
    "message": "通知创建成功",
    "data": {
        "id": 789,
        "notification_uuid": "550e8400-e29b-41d4-a716-446655440005",
        "user_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "type": 0,
        "title": "订单状态更新",
        "content": "您的订单 123 状态已更新为：已支付",
        "is_read": false,
        "created_at": "2025-01-01T12:00:00Z"
    }
}
```

**失败响应:**
```json
{
    "code": "400",
    "message": "Invalid user_uuid or required fields missing",
    "data": null
}
```

**错误处理:** 如果调用失败，记录警告日志，不影响主业务流程

---

## 8.2 PaymentService 发起的调用

### 调用 OrderService - 验证订单
**场景:** 创建支付前验证订单存在且状态正确

**调用接口:**
```
GET /api/orders/internal/{order_uuid}/
```

**请求示例:**
```http
GET /api/orders/internal/550e8400-e29b-41d4-a716-446655440000/
```

**成功响应:**
```json
{
    "success": true,
    "data": {
        "order_id": 123,
        "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "buyer_uuid": "550e8400-e29b-41d4-a716-446655440001",
        "seller_uuid": "550e8400-e29b-41d4-a716-446655440002",
        "total_amount": "199.98",
        "status": 0,
        "created_at": "2025-01-01T12:00:00Z",
        "shipping_address": "配送地址",
        "products": [
            {
                "product_uuid": "028a38c7-506e-4e13-9c84-2a7ba4165aae",
                "product_name": "商品名称",
                "quantity": 2,
                "price": "99.99"
            }
        ]
    }
}
```

**失败响应:**
```json
{
    "code": "404",
    "message": "订单不存在",
    "data": null
}
```

---

### 调用 OrderService - 更新订单状态
**场景:** 支付成功后更新订单状态为已支付

**调用接口:**
```
PATCH /api/orders/internal/orders/{order_uuid}/
```

**请求示例:**
```http
PATCH /api/orders/internal/orders/550e8400-e29b-41d4-a716-446655440000/
Content-Type: application/json

{
    "status": 1,
    "payment_time": "2025-01-01T12:05:00Z",
    "payment_method": 0
}
```

**成功响应:**
```json
{
    "code": "200",
    "message": "订单状态更新成功",
    "data": {
        "order_id": 123,
        "order_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "status": 1,
        "payment_time": "2025-01-01T12:05:00Z",
        "updated_at": "2025-01-01T12:05:00Z"
    }
}
```

**失败响应:**
```json
{
    "code": "400",
    "message": "订单不存在或状态不允许更新",
    "data": null
}
```

---

## 8.3 跨服务调用的数据流

### 完整的订单创建流程调用链:
```
1. 用户调用: POST /api/orders/
2. OrderService → ProductService: 验证商品信息
3. OrderService → OrderService: 创建订单
4. OrderService → NotificationService: 发送创建通知
5. 返回: 订单创建成功响应
```

### 完整的支付流程调用链:
```
1. 用户调用: POST /api/payment/create/
2. PaymentService → OrderService: 验证订单状态
3. PaymentService → PaymentService: 创建支付记录
4. PaymentService → 第三方支付: 创建支付订单
5. 第三方支付回调: POST /api/payment/callback/{method}/
6. PaymentService → OrderService: 更新订单状态
7. OrderService → NotificationService: 发送支付成功通知
8. 返回: 支付处理结果
```

### 订单状态变更流程调用链:
```
1. 用户调用: PUT /api/orders/{order_id}/
2. OrderService → OrderService: 更新订单状态
3. OrderService → NotificationService: 发送状态变更通知
4. 返回: 更新成功响应
```

---

# 9. 错误响应格式

```json
{
    "code": "400",
    "message": "错误描述",
    "data": null
}
```

常见错误码:
- 400: 请求参数错误
- 401: 用户身份验证失败
- 404: 资源不存在
- 500: 服务器内部错误

---

# 10. 认证机制

系统使用 Spring Cloud Gateway 进行统一认证，微服务间通过 HTTP Header 传递用户UUID：
```
X-User-UUID: 550e8400-e29b-41d4-a716-446655440001
```

内部微服务接口 (以 `/internal/` 开头的路径) 无需用户认证。
