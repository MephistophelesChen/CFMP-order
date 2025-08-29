@echo off
chcp 65001 >nul
echo.
echo ==========================================
rem 使用 PowerShell 打印中文，避免编码问题
powershell -NoProfile -Command "Write-Host ' CFMP微服务系统启动脚本 (MySQL+Redis+微服务)'"
echo ==========================================
echo.

powershell -NoProfile -Command "Write-Host '[1/3] 启动基础设施 (MySQL + Redis)...'"
docker-compose up -d mysql redis

echo.
powershell -NoProfile -Command "Write-Host '[2/3] 等待基础设施就绪 (20秒)...'"
timeout /t 20 /nobreak >nul

echo.
powershell -NoProfile -Command "Write-Host '[3/3] 启动微服务...'"
docker-compose up -d order-service payment-service notification-service

echo.
echo ==========================================
powershell -NoProfile -Command "Write-Host ' 启动完成！'"
echo ==========================================
echo.
powershell -NoProfile -Command "Write-Host '服务地址：'"
powershell -NoProfile -Command "Write-Host '  订单服务:   http://localhost:8001'"
powershell -NoProfile -Command "Write-Host '  支付服务:   http://localhost:8002'"
powershell -NoProfile -Command "Write-Host '  通知服务:   http://localhost:8003'"
powershell -NoProfile -Command "Write-Host '  MySQL数据库: localhost:3306'"
powershell -NoProfile -Command "Write-Host '  Redis缓存:  localhost:6379'"
echo.
powershell -NoProfile -Command "Write-Host '外部服务：'"
powershell -NoProfile -Command "Write-Host '  Nacos控制台: http://123.57.145.79:8848/nacos'"
echo.
powershell -NoProfile -Command "Write-Host '查看服务状态: docker-compose ps'"
powershell -NoProfile -Command "Write-Host '查看服务日志: docker-compose logs [service-name]'"
echo.

pause
