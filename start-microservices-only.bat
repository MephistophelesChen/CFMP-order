@echo off
chcp 65001 >nul
echo.
echo ==========================================
echo  CFMP微服务系统 - MySQL + 微服务
echo ==========================================
echo.
echo 此脚本部署MySQL和微服务
echo 使用外部Nacos服务: 123.57.145.79:8848
echo.

docker-compose -f docker-compose-services.yml up -d

echo.
echo ==========================================
echo  微服务启动完成！
echo ==========================================
echo.
echo 服务地址：
echo   订单服务:   http://localhost:8001
echo   支付服务:   http://localhost:8002
echo   通知服务:   http://localhost:8003
echo   MySQL数据库: localhost:3306
echo.
echo 外部服务：
echo   Nacos控制台: http://123.57.145.79:8848/nacos
echo.

pause
