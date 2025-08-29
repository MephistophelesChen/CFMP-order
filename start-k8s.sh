#!/bin/bash
# start-k8s.sh

echo "启动 CFMP Kubernetes 应用..."




# 构建镜像
echo "构建订单服务镜像..."
docker build -t order-service -f Dockerfile.order-root .

echo "构建支付服务镜像..."
docker build -t payment-service -f Dockerfile.payment-root .

echo "构建通知服务镜像..."
docker build -t notification-service -f Dockerfile.notification-root .

export KUBECTL="k3s kubectl"

# 若存在 k3s，则将镜像导入到 k3s 的 containerd 中
if command -v k3s >/dev/null 2>&1; then
  echo "将镜像导入 K3s..."
  docker save order-service:latest -o order-service.tar
  k3s ctr images import order-service.tar
  rm -f order-service.tar || true

  docker save payment-service:latest -o payment-service.tar
  k3s ctr images import payment-service.tar
  rm -f payment-service.tar || true

  docker save notification-service:latest -o notification-service.tar
  k3s ctr images import notification-service.tar
  rm -f notification-service.tar || true
else
  echo "未检测到 k3s，跳过 ctr 导入。请确保集群节点可访问到该镜像（例如在同一 Docker 宿主或推送到镜像仓库）。"
fi

# 处理 MySQL 镜像
echo "准备 mysql:8.0 镜像..."
# docker pull mysql:8.0 || true
if command -v k3s >/dev/null 2>&1; then
  echo "将 mysql:8.0 镜像导入 K3s..."
  docker save mysql:8.0 -o mysql.tar
  k3s ctr images import mysql.tar
  rm -f mysql.tar || true
fi

# 部署应用
echo "部署应用..."
$KUBECTL apply -f k8s/namespace.yaml

# 确保 MySQL 初始化 ConfigMap 存在（从 sql/init.sql 创建/更新）
echo "创建/更新 MySQL 初始化 ConfigMap..."
$KUBECTL -n cfmp-order create configmap mysql-init-config --from-file=init.sql=sql/init.sql --dry-run=client -o yaml | $KUBECTL apply -f -

$KUBECTL delete -f k8s/mysql-deployment.yaml \
                 -f k8s/order-service.yaml \
                 -f k8s/payment-service.yaml \
                 -f k8s/notification-service.yaml \
                 --ignore-not-found=true || true
sleep 3
$KUBECTL apply -f k8s/mysql-deployment.yaml
$KUBECTL apply -f k8s/order-service.yaml
$KUBECTL apply -f k8s/payment-service.yaml
$KUBECTL apply -f k8s/notification-service.yaml

# 等待启动
echo "等待应用启动..."
$KUBECTL -n cfmp-order wait --for=condition=ready pod -l app=mysql --timeout=300s || true
$KUBECTL -n cfmp-order wait --for=condition=ready pod -l app=order-service --timeout=300s || true
$KUBECTL -n cfmp-order wait --for=condition=ready pod -l app=payment-service --timeout=300s || true
$KUBECTL -n cfmp-order wait --for=condition=ready pod -l app=notification-service --timeout=300s || true

# 运行数据库迁移
echo "运行数据库迁移..."
$KUBECTL -n cfmp-order exec deploy/order-service -- python manager.py migrate --noinput || true
$KUBECTL -n cfmp-order exec deploy/payment-service -- python manager.py migrate --noinput || true
$KUBECTL -n cfmp-order exec deploy/notification-service -- python manager.py migrate --noinput || true

# 显示访问地址
echo ""
echo "部署完成！访问地址："
echo "订单服务端口: 30001 (NodePort)"
echo "支付服务端口: 30002 (NodePort)"
echo "通知服务端口: 30003 (NodePort)"
echo ""
$KUBECTL -n cfmp-order get pods -o wide
$KUBECTL -n cfmp-order get services

echo "提示：若未使用 K3s 或节点无法直接访问本地镜像，请将镜像推送到可达的镜像仓库后再部署。"
