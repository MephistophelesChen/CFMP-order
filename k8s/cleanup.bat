@echo off
chcp 65001 >nul
echo Kubernetes微服务清理脚本

echo 正在删除CFMP微服务部署...

kubectl delete -f notification-service.yaml
kubectl delete -f payment-service.yaml
kubectl delete -f order-service.yaml
kubectl delete -f mysql-deployment.yaml
kubectl delete -f namespace.yaml

echo 清理完成！

pause
