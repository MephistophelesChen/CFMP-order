# CFMP微服务启动脚本
# 使用根目录下的Dockerfile以包含common模块

Write-Host "=== CFMP微服务启动脚本 ===" -ForegroundColor Green

# 外部服务配置
$NACOS_SERVER = "123.57.145.79:8848"
$DB_HOST = "123.57.145.79"
$DB_USER = "cfmp_user"
$DB_PASSWORD = "cfmp123456"
$DB_PORT = "3306"

Write-Host "外部服务配置:" -ForegroundColor Yellow
Write-Host "  Nacos: $NACOS_SERVER" -ForegroundColor Cyan
Write-Host "  MySQL: ${DB_HOST}:${DB_PORT}" -ForegroundColor Cyan

# 清理现有容器（如果存在）
Write-Host "`n清理现有容器..." -ForegroundColor Yellow
docker stop order-service-fixed payment-service-v1 notification-service-v1 2>$null
docker rm order-service-fixed payment-service-v1 notification-service-v1 2>$null

# 构建镜像
Write-Host "`n构建Docker镜像..." -ForegroundColor Yellow
Write-Host "构建order-service..." -ForegroundColor Cyan
docker build -f Dockerfile.order-root -t order-service:latest .

Write-Host "构建payment-service..." -ForegroundColor Cyan
docker build -f Dockerfile.payment-root -t payment-service:latest .

Write-Host "构建notification-service..." -ForegroundColor Cyan
docker build -f Dockerfile.notification-root -t notification-service:latest .

# 启动微服务
Write-Host "`n启动微服务..." -ForegroundColor Yellow

Write-Host "启动订单服务 (端口8001)..." -ForegroundColor Cyan
docker run -d --name order-service `
    -p 8001:8001 `
    -e CFMP_DB_HOST=$DB_HOST `
    -e CFMP_DB_NAME=cfmp_order `
    -e CFMP_DB_USER=$DB_USER `
    -e CFMP_DB_PASSWORD=$DB_PASSWORD `
    -e CFMP_DB_PORT=$DB_PORT `
    -e NACOS_SERVER=$NACOS_SERVER `
    order-service:latest

Write-Host "启动支付服务 (端口8002)..." -ForegroundColor Cyan
docker run -d --name payment-service `
    -p 8002:8002 `
    -e CFMP_DB_HOST=$DB_HOST `
    -e CFMP_DB_NAME=cfmp_payment `
    -e CFMP_DB_USER=$DB_USER `
    -e CFMP_DB_PASSWORD=$DB_PASSWORD `
    -e CFMP_DB_PORT=$DB_PORT `
    -e NACOS_SERVER=$NACOS_SERVER `
    payment-service:latest

Write-Host "启动通知服务 (端口8003)..." -ForegroundColor Cyan
docker run -d --name notification-service `
    -p 8003:8003 `
    -e CFMP_DB_HOST=$DB_HOST `
    -e CFMP_DB_NAME=cfmp_notification `
    -e CFMP_DB_USER=$DB_USER `
    -e CFMP_DB_PASSWORD=$DB_PASSWORD `
    -e CFMP_DB_PORT=$DB_PORT `
    -e NACOS_SERVER=$NACOS_SERVER `
    notification-service:latest

# 等待服务启动
Write-Host "`n等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host "`n检查服务状态:" -ForegroundColor Yellow
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host "`n=== 微服务启动完成 ===" -ForegroundColor Green
Write-Host "服务端点:" -ForegroundColor Yellow
Write-Host "  订单服务: http://localhost:8001" -ForegroundColor Cyan
Write-Host "  支付服务: http://localhost:8002" -ForegroundColor Cyan
Write-Host "  通知服务: http://localhost:8003" -ForegroundColor Cyan
Write-Host "`n查看服务日志: docker logs [service-name]" -ForegroundColor Yellow
