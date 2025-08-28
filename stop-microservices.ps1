# CFMP微服务停止脚本

Write-Host "=== CFMP微服务停止脚本 ===" -ForegroundColor Red

Write-Host "停止微服务容器..." -ForegroundColor Yellow
docker stop order-service payment-service notification-service 2>$null

Write-Host "删除微服务容器..." -ForegroundColor Yellow
docker rm order-service payment-service notification-service 2>$null

Write-Host "清理旧版本容器..." -ForegroundColor Yellow
docker stop order-service-fixed payment-service-v1 notification-service-v1 2>$null
docker rm order-service-fixed payment-service-v1 notification-service-v1 2>$null

Write-Host "`n检查剩余容器:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n=== 微服务已停止 ===" -ForegroundColor Red
