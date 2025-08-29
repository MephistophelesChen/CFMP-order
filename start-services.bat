@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo  CFMP微服务系统启动脚本 (MySQL+Redis+微服务)
echo ==========================================
echo.

echo [1/3] 启动基础设施 (MySQL + Redis)...
docker-compose up -d mysql redis

echo.
echo [2/3] 等待基础设施就绪 (20秒)...
timeout /t 20 /nobreak >nul

echo.
echo [3/3] 启动微服务...
docker-compose up -d order-service payment-service notification-service

echo.
echo ==========================================
echo  启动完成！
echo ==========================================
echo.
echo 服务地址：
echo   订单服务:   http://localhost:8001
echo   支付服务:   http://localhost:8002
echo   通知服务:   http://localhost:8003
echo   MySQL数据库: localhost:3306
echo   Redis缓存:  localhost:6379
echo.
echo 外部服务：
echo   Nacos控制台: http://123.57.145.79:8848/nacos
echo.
echo 查看服务状态: docker-compose ps
echo 查看服务日志: docker-compose logs [service-name]
echo.

pause
