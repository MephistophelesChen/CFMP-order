#!/bin/bash
# start-k8s-simple.sh - 简化版K8s部署脚本，适用于CI/CD环境

# 设置kubectl别名
export KUBECTL="k3s kubectl"

# 检查k3s是否可用
if ! command -v k3s >/dev/null 2>&1; then
    echo "错误: 未检测到 k3s"
    exit 1
fi

# 构建镜像（带超时保护）
echo "1. 构建服务镜像..."
timeout 300 docker build -t order-service:latest -f Dockerfile.order-root . || { echo "订单服务构建失败"; exit 1; }
timeout 300 docker build -t payment-service:latest -f Dockerfile.payment-root . || { echo "支付服务构建失败"; exit 1; }
timeout 300 docker build -t notification-service:latest -f Dockerfile.notification-root . || { echo "通知服务构建失败"; exit 1; }

# 导入镜像到k3s
echo "2. 导入镜像到 K3s..."
for service in order-service payment-service notification-service; do
    echo "  导入 $service..."
    docker save $service:latest -o ${service}.tar
    k3s ctr images import ${service}.tar
    rm -f ${service}.tar
done

# 导入MySQL镜像
# echo "  导入 mysql:8.0..."
# docker save mysql:8.0 -o mysql.tar
# k3s ctr images import mysql.tar
# rm -f mysql.tar

# 部署到k8s
echo "3. 部署到 Kubernetes..."
$KUBECTL apply -f k8s/namespace.yaml

# 创建MySQL配置
echo "4. 创建 MySQL 配置..."
$KUBECTL -n cfmp-order create configmap mysql-init-config --from-file=init.sql=sql/init.sql --dry-run=client -o yaml | $KUBECTL apply -f -

# 等待ConfigMap创建完成
echo "  等待ConfigMap创建完成..."
sleep 2

# 删除旧部署（保留数据存储，但不删除MySQL）
echo "5. 清理旧应用服务部署..."
$KUBECTL delete -f k8s/order-service.yaml -f k8s/payment-service.yaml -f k8s/notification-service.yaml --ignore-not-found=true
sleep 5

# 部署新版本
# echo "6. 首先部署MySQL..."
# $KUBECTL apply -f k8s/mysql-deployment.yaml

# # 等待MySQL完全启动
# echo "7. 等待MySQL完全启动..."
# $KUBECTL -n cfmp-order wait --for=condition=ready pod -l app=mysql-service --timeout=300s
# echo "  MySQL已就绪，开始部署应用服务..."



# 部署应用服务
echo "8. 部署应用服务..."
$KUBECTL apply -f k8s/order-service.yaml
$KUBECTL apply -f k8s/payment-service.yaml
$KUBECTL apply -f k8s/notification-service.yaml

# 部署自动扩缩容配置
echo "9. 部署自动扩缩容..."
$KUBECTL apply -f k8s/hpa-optimized.yaml
$KUBECTL apply -f k8s/pdb.yaml
$KUBECTL apply -f k8s/circuit-breaker.yaml

# 等待服务部署完成
echo "10. 等待应用服务启动（30秒）..."
sleep 30
echo "  检查服务状态..."
$KUBECTL -n cfmp-order get pods

#


# 运行数据库迁移
echo "11. 生成并执行数据库迁移..."

# # 首先生成迁移文件 (makemigrations)
# echo "  生成迁移文件..."
# $KUBECTL -n cfmp-order exec deploy/order-service -- python manage.py makemigrations --noinput
# $KUBECTL -n cfmp-order exec deploy/payment-service -- python manage.py makemigrations --noinput
# $KUBECTL -n cfmp-order exec deploy/notification-service -- python manage.py makemigrations --noinput

# # 然后执行迁移 (migrate)
# echo "  执行数据库迁移..."
# $KUBECTL -n cfmp-order exec deploy/order-service -- python manage.py migrate --noinput
# $KUBECTL -n cfmp-order exec deploy/payment-service -- python manage.py migrate --noinput
# $KUBECTL -n cfmp-order exec deploy/notification-service -- python manage.py migrate --noinput

# # 检查迁移状态
# echo "  检查迁移状态..."
# $KUBECTL -n cfmp-order exec deploy/order-service -- python manage.py showmigrations
# $KUBECTL -n cfmp-order exec deploy/payment-service -- python manage.py showmigrations
# $KUBECTL -n cfmp-order exec deploy/notification-service -- python manage.py showmigrations

# 显示部署状态
echo "12. 部署状态:"
$KUBECTL -n cfmp-order get pods -o wide
$KUBECTL -n cfmp-order get services
$KUBECTL -n cfmp-order get hpa
$KUBECTL -n cfmp-order get pdb

echo "=== CFMP K8s 部署完成 ==="
echo "访问端口: 订单服务(30001), 支付服务(30002), 通知服务(30003)"
echo "自动扩缩容已启用，监控和告警已配置"
