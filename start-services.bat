@echo off
chcp 65001 >nul
REM 微服务启动脚本 - Windows版本

echo 启动CFMP微服务系统...

REM 环境变量应该在系统中预先设置，这里只是示例
REM 请在系统环境变量中设置以下变量：
REM NACOS_SERVER=your_nacos_server:8848
REM NACOS_NAMESPACE=your_namespace
REM NACOS_USERNAME=your_username
REM NACOS_PASSWORD=your_password
REM SERVICE_IP=your_service_ip

REM 启动订单服务 (端口8001)
echo 启动订单服务...
cd order-service
set SERVICE_PORT=8001
start "Order Service" cmd /k "chcp 65001 >nul && python manage.py runserver 0.0.0.0:8001"
cd ..

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 启动支付服务 (端口8002)
echo 启动支付服务...
cd payment-service
set SERVICE_PORT=8002
start "Payment Service" cmd /k "chcp 65001 >nul && python manage.py runserver 0.0.0.0:8002"
cd ..

REM 等待2秒
timeout /t 2 /nobreak >nul

REM 启动通知服务 (端口8003)
echo 启动通知服务...
cd notification-service
set SERVICE_PORT=8003
start "Notification Service" cmd /k "chcp 65001 >nul && python manage.py runserver 0.0.0.0:8003"
cd ..

echo 所有服务已启动:
echo - 订单服务: http://localhost:8001
echo - 支付服务: http://localhost:8002
echo - 通知服务: http://localhost:8003
echo.
echo 每个服务都在独立的命令窗口中运行
echo 关闭相应的命令窗口即可停止对应的服务
pause
