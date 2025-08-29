@echo off
chcp 65001 >nul
echo.
echo ==========================================
powershell -NoProfile -Command "Write-Host ' CFMP微服务系统停止脚本'"
echo ==========================================
echo.

echo [1/2] 停止所有服务...
docker-compose down

echo.
echo [2/2] 清理容器和网络...
docker system prune -f

echo.
echo ==========================================
powershell -NoProfile -Command "Write-Host ' 所有服务已停止！'"
echo ==========================================
echo.

pause
