@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 动态端口微服务启动脚本

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请确保Python已安装并在PATH中
    pause
    exit /b 1
)

echo 正在启动微服务（动态端口模式）...
echo.

REM 启动订单服务
echo [1/3] 启动订单服务...
start "Order Service" cmd /c "python dynamic_port_launcher.py order-service --port 8001 --name OrderService & pause"

REM 等待3秒
echo 等待订单服务启动...
timeout /t 3 /nobreak >nul

REM 启动支付服务
echo [2/3] 启动支付服务...
start "Payment Service" cmd /c "python dynamic_port_launcher.py payment-service --port 8002 --name PaymentService & pause"

REM 等待3秒
echo 等待支付服务启动...
timeout /t 3 /nobreak >nul

REM 启动通知服务
echo [3/3] 启动通知服务...
start "Notification Service" cmd /c "python dynamic_port_launcher.py notification-service --port 8003 --name NotificationService & pause"

echo.
echo ================================================
echo                启动完成！
echo ================================================
echo.
echo ✓ 所有服务已在独立窗口中启动
echo ✓ 如果首选端口被占用，系统会自动分配可用端口
echo ✓ 服务发现通过Nacos自动处理端口变化
echo.
echo 提示:
echo - 查看各服务窗口确认实际端口号
echo - 关闭服务窗口即可停止对应服务
echo - 服务注册信息可在Nacos控制台查看
echo.
pause
