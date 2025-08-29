# CFMP-Order Kubernetes部署指南

本项目提供了完整的Kubernetes部署配置，可以在本地Kubernetes环境中运行CFMP微服务系统。

## 前置条件

1. **Docker Desktop** - 已安装并启用Kubernetes
2. **kubectl** - Kubernetes命令行工具
3. **已构建的Docker镜像**：
   - `order-service:latest`
   - `payment-service:latest`
   - `notification-service:latest`

## 部署组件

### 基础设施组件
- **MySQL 8.0** - 数据库服务（容器化部署）

### 微服务组件
- **订单服务** (order-service) - 端口8001
- **支付服务** (payment-service) - 端口8002
- **通知服务** (notification-service) - 端口8003

### 外部服务
- **Nacos 2.3.0** - 服务注册与发现（外部：123.57.145.79:8848）

## 快速部署

### Windows环境

```cmd
cd k8s
deploy.bat
```

### 查看状态

```cmd
status.bat
```

### 清理部署

```cmd
cleanup.bat
```

## 手动部署步骤

1. **创建命名空间**
   ```bash
   kubectl apply -f namespace.yaml
   ```

2. **部署MySQL数据库**
   ```bash
   kubectl apply -f mysql-deployment.yaml
   ```

3. **部署微服务**
   ```bash
   kubectl apply -f order-service.yaml
   kubectl apply -f payment-service.yaml
   kubectl apply -f notification-service.yaml
   ```

## 访问地址

部署完成后，可以通过以下地址访问服务：

- **订单服务**: http://localhost:30001
- **支付服务**: http://localhost:30002
- **通知服务**: http://localhost:30003

**外部服务**:
- **Nacos控制台**: http://123.57.145.79:8848/nacos

## 管理命令

### 查看服务状态
```cmd
status.bat
```
或
```bash
kubectl get pods -n cfmp-order
kubectl get services -n cfmp-order
```

### 查看日志
```bash
kubectl logs deployment/order-service -n cfmp-order
kubectl logs deployment/payment-service -n cfmp-order
kubectl logs deployment/notification-service -n cfmp-order
kubectl logs deployment/mysql -n cfmp-order
```

### 清理部署
```cmd
cleanup.bat
```

## 配置说明

### 资源限制
每个微服务都配置了资源限制：
- **请求**: 256Mi内存, 200m CPU
- **限制**: 512Mi内存, 500m CPU

MySQL数据库：
- **请求**: 512Mi内存, 300m CPU
- **限制**: 1Gi内存, 500m CPU

### 健康检查
- **微服务就绪检查**: 30秒后开始，每5秒检查一次
- **微服务存活检查**: 60秒后开始，每10秒检查一次
- **MySQL健康检查**: 30秒后开始就绪检查，60秒后开始存活检查

### 数据持久化
- MySQL使用emptyDir卷，重启Pod会丢失数据
- 生产环境建议使用PersistentVolume

## 故障排除

### 常见问题

1. **Pod启动失败**
   ```bash
   kubectl describe pod <pod-name> -n cfmp-order
   kubectl logs <pod-name> -n cfmp-order
   ```

2. **镜像拉取失败**
   - 确保Docker镜像已构建
   - 检查imagePullPolicy设置为Never

3. **服务无法访问**
   - 检查Service和Pod标签匹配
   - 验证端口配置正确

4. **数据库连接失败**
   - 确保MySQL Pod正常运行
   - 检查数据库初始化脚本执行情况

5. **Nacos连接失败**
   - 检查外部Nacos服务是否可访问：123.57.145.79:8848
   - 验证网络连接

### 调试命令

```bash
# 进入Pod调试
kubectl exec -it deployment/order-service -n cfmp-order -- /bin/bash

# 端口转发到本地
kubectl port-forward service/order-service 8001:8001 -n cfmp-order

# 查看事件
kubectl get events -n cfmp-order --sort-by='.lastTimestamp'
```

## 扩缩容

```bash
# 扩展订单服务到3个副本
kubectl scale deployment order-service --replicas=3 -n cfmp-order

# 查看副本状态
kubectl get deployment order-service -n cfmp-order
```

## 监控

可以集成Prometheus和Grafana进行监控：

```bash
# 安装Prometheus Operator (可选)
kubectl apply -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/main/bundle.yaml
```
