@echo off
chcp 65001 >nul
echo 查看CFMP微服务状态

echo ==========================================
echo  Pods状态
echo ==========================================
kubectl get pods -n cfmp-order

echo.
echo ==========================================
echo  Services状态
echo ==========================================
kubectl get services -n cfmp-order

echo.
echo ==========================================
echo  部署状态
echo ==========================================
kubectl get deployments -n cfmp-order

echo.
echo 查看Pod日志命令：
echo   kubectl logs deployment/order-service -n cfmp-order
echo   kubectl logs deployment/payment-service -n cfmp-order
echo   kubectl logs deployment/notification-service -n cfmp-order

pause
