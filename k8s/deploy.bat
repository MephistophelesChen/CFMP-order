@echo off
chcp 65001 >nul
echo 部署CFMP微服务到Kubernetes

echo 1. 创建命名空间...
kubectl apply -f namespace.yaml

echo 2. 部署MySQL数据库...
kubectl apply -f mysql-deployment.yaml

echo 3. 等待MySQL就绪...
timeout /t 30 /nobreak >nul

echo 4. 部署微服务...
kubectl apply -f order-service.yaml
kubectl apply -f payment-service.yaml
kubectl apply -f notification-service.yaml

echo 部署完成！

echo.
echo 查看部署状态：
kubectl get pods -n cfmp-order
kubectl get services -n cfmp-order

echo.
echo 服务访问地址：
echo   订单服务: http://localhost:30001
echo   支付服务: http://localhost:30002
echo   通知服务: http://localhost:30003
echo.
echo 外部服务：
echo   Nacos控制台: http://123.57.145.79:8848/nacos

pause
