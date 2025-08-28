#!/bin/bash
# 微服务启动脚本 - Linux/Mac版本

echo "启动CFMP微服务系统..."

# 设置环境变量
export NACOS_SERVER="123.57.145.79:8848"
export NACOS_NAMESPACE="public"
export NACOS_USERNAME="nacos"
export NACOS_PASSWORD="no5groupnacos"
export SERVICE_IP="123.57.145.79"  # 替换为您的实际IP地址

# 启动订单服务 (端口8001)
echo "启动订单服务..."
cd order-service
export SERVICE_PORT=8001
python manage.py runserver 0.0.0.0:8001 &
ORDER_PID=$!
cd ..

# 启动支付服务 (端口8002)
echo "启动支付服务..."
cd payment-service
export SERVICE_PORT=8002
python manage.py runserver 0.0.0.0:8002 &
PAYMENT_PID=$!
cd ..

# 启动通知服务 (端口8003)
echo "启动通知服务..."
cd notification-service
export SERVICE_PORT=8003
python manage.py runserver 0.0.0.0:8003 &
NOTIFICATION_PID=$!
cd ..

echo "所有服务已启动："
echo "- 订单服务: http://0.0.0.0:8001 (PID: $ORDER_PID)"
echo "- 支付服务: http://0.0.0.0:8002 (PID: $PAYMENT_PID)"
echo "- 通知服务: http://0.0.0.0:8003 (PID: $NOTIFICATION_PID)"

# 等待用户输入以停止服务
echo "按任意键停止所有服务..."
read -n 1

# 停止所有服务
echo "停止所有服务..."
kill $ORDER_PID $PAYMENT_PID $NOTIFICATION_PID
echo "所有服务已停止"
