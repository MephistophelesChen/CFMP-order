@echo off
chcp 65001 >nul
echo.
echo ==========================================
powershell -NoProfile -Command "Write-Host ' CFMP微服务系统 - MySQL + 微服务'"
echo ==========================================
echo.
powershell -NoProfile -Command "Write-Host '此脚本部署MySQL和微服务'"
powershell -NoProfile -Command "Write-Host '使用外部Nacos服务: 123.57.145.79:8848'"
echo.

docker-compose -f docker-compose-services.yml up -d

echo.
echo ==========================================
powershell -NoProfile -Command "Write-Host ' 微服务启动完成！'"
echo ==========================================
echo.
powershell -NoProfile -Command "Write-Host '服务地址：'"
powershell -NoProfile -Command "Write-Host '  订单服务:   http://localhost:8001'"
powershell -NoProfile -Command "Write-Host '  支付服务:   http://localhost:8002'"
powershell -NoProfile -Command "Write-Host '  通知服务:   http://localhost:8003'"
powershell -NoProfile -Command "Write-Host '  MySQL数据库: localhost:3306'"
echo.
powershell -NoProfile -Command "Write-Host '外部服务：'"
powershell -NoProfile -Command "Write-Host '  Nacos控制台: http://123.57.145.79:8848/nacos'"
echo.

pause
