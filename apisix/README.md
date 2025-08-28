# CFMP订单系统 - Apisix网关用户认证配置指南

## 概述

本文档说明如何配置Apisix网关，使其能够从JWT token中解析用户UUID并通过HTTP头传递给下游微服务。

## 核心机制

### 1. JWT Token解析
- Apisix网关接收到包含JWT token的请求
- 使用`jwt-auth`插件验证token有效性
- 使用`serverless-pre-function`插件解析token payload

### 2. 用户UUID传递
网关解析JWT token后，将用户UUID添加到以下HTTP头中：
- `X-User-UUID`: 主要的用户UUID字段
- `X-User-ID`: 备用的用户ID字段（兼容性）
- `X-JWT-User-UUID`: 从JWT payload直接提取的用户UUID

### 3. 微服务接收
下游微服务（订单、支付、通知服务）通过以下方式获取用户UUID：

```python
def _get_user_uuid_from_request(self):
    """从Apisix网关解析的请求头中获取用户UUID"""
    # 方案1：从Apisix网关添加的HTTP头获取用户UUID
    user_uuid = self.request.META.get('HTTP_X_USER_UUID')
    if user_uuid:
        return user_uuid

    # 方案2：从其他可能的头字段获取
    user_uuid = self.request.META.get('HTTP_X_USER_ID')
    if user_uuid:
        return user_uuid

    # 方案3：从JWT payload中获取（如果Apisix解析并添加到头中）
    user_uuid = self.request.META.get('HTTP_X_JWT_USER_UUID')
    if user_uuid:
        return user_uuid

    # 兼容性：开发环境下的备用方案
    if hasattr(self.request, 'user') and self.request.user.is_authenticated:
        return getattr(self.request.user, 'uuid', None)

    return None
```

## 配置步骤

### 1. JWT Secret配置
在`apisix.yaml`中设置正确的JWT secret：

```yaml
jwt-auth:
  header: Authorization
  query: jwt
  cookie: jwt
  hide_credentials: false
  secret: "your-actual-jwt-secret"  # 替换为实际的JWT密钥
```

### 2. JWT Payload格式要求
JWT token的payload应包含以下字段之一：
- `user_uuid`: 推荐使用，明确表示用户UUID
- `sub`: 标准JWT subject字段，可用作用户ID
- `user_id`: 备用用户ID字段

示例JWT payload：
```json
{
  "user_uuid": "123e4567-e89b-12d3-a456-426614174000",
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "exp": 1735689600,
  "iat": 1735603200
}
```

### 3. 网关路由配置
每个微服务路由都需要配置JWT认证和用户信息提取：

```yaml
routes:
  - id: notification-service
    uri: /api/notifications/*
    upstream:
      nodes:
        "notification-service:8004": 1
    plugins:
      jwt-auth:
        header: Authorization
      serverless-pre-function:
        phase: rewrite
        functions:
          - |
            return function(conf, ctx)
              local core = require("apisix.core")
              local jwt = require("resty.jwt")

              local auth_header = core.request.header(ctx, "Authorization")
              if auth_header and string.find(auth_header, "Bearer ") then
                local token = string.sub(auth_header, 8)
                local jwt_obj = jwt:verify("your-jwt-secret", token)
                if jwt_obj and jwt_obj.valid then
                  local user_uuid = jwt_obj.payload.user_uuid or jwt_obj.payload.sub
                  if user_uuid then
                    core.request.set_header(ctx, "X-User-UUID", user_uuid)
                  end
                end
              end
            end
```

## 优势

### 1. 性能优化
- 避免每次请求都调用UserService验证token
- 减少微服务间的网络调用
- 降低系统延迟

### 2. 架构简化
- 统一在网关层处理用户认证
- 微服务只需要关注业务逻辑
- 减少代码重复

### 3. 安全性增强
- 集中的JWT验证逻辑
- 统一的用户身份管理
- 便于安全策略的实施

## 测试验证

### 1. 测试JWT解析
```bash
# 发送带JWT token的请求
curl -H "Authorization: Bearer <your-jwt-token>" \
     http://localhost:9080/api/notifications/

# 检查微服务日志，确认收到X-User-UUID头
```

### 2. 调试网关配置
```bash
# 查看Apisix网关日志
docker logs apisix-gateway

# 查看微服务日志中的用户UUID
docker logs notification-service
```

## 故障排除

### 1. 用户UUID为空
- 检查JWT token格式是否正确
- 确认JWT secret配置是否匹配
- 验证JWT payload中是否包含用户UUID字段

### 2. 认证失败
- 检查Authorization头格式（Bearer <token>）
- 确认JWT token未过期
- 验证Apisix网关配置是否生效

## 注意事项

1. **JWT Secret安全**: 确保JWT secret在生产环境中足够复杂且保密
2. **Token过期处理**: 客户端需要处理token过期的情况
3. **兼容性保留**: 现有代码保留了开发环境下的兼容性处理
4. **日志记录**: 建议记录用户UUID获取的过程以便调试

## 后续改进

1. **动态JWT Secret**: 支持从配置中心动态获取JWT secret
2. **多租户支持**: 支持多租户场景下的用户隔离
3. **性能监控**: 添加用户认证相关的性能指标
4. **缓存优化**: 考虑在网关层缓存用户信息以进一步提升性能
