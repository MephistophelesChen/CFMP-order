#!/usr/bin/env python
"""
Nacos服务注册测试脚本
用于测试微服务是否成功注册到Nacos
"""

import requests
import time
import json
import os

# Nacos配置 - 从环境变量获取
NACOS_SERVER = os.getenv('NACOS_SERVER', '127.0.0.1:8848')
NACOS_USERNAME = os.getenv('NACOS_USERNAME', 'nacos')
NACOS_PASSWORD = os.getenv('NACOS_PASSWORD', 'nacos')
NAMESPACE = os.getenv('NACOS_NAMESPACE', 'public')

def test_nacos_connection():
    """测试Nacos连接"""
    try:
        url = f"http://{NACOS_SERVER}/nacos/v1/console/health"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ Nacos服务器连接正常")
            return True
        else:
            print(f"❌ Nacos服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接Nacos服务器失败: {e}")
        return False

def get_nacos_token():
    """获取Nacos访问令牌"""
    try:
        url = f"http://{NACOS_SERVER}/nacos/v1/auth/login"
        data = {
            'username': NACOS_USERNAME,
            'password': NACOS_PASSWORD
        }
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            return result.get('accessToken', '')
        return ''
    except Exception as e:
        print(f"❌ 获取Nacos令牌失败: {e}")
        return ''

def check_service_registration(service_name, token=''):
    """检查服务注册状态"""
    try:
        url = f"http://{NACOS_SERVER}/nacos/v1/ns/instance/list"
        params = {
            'serviceName': service_name,
            'namespaceId': NAMESPACE
        }
        if token:
            params['accessToken'] = token

        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            result = response.json()
            hosts = result.get('hosts', [])
            if hosts:
                print(f"✅ 服务 {service_name} 已注册，实例数: {len(hosts)}")
                for i, host in enumerate(hosts):
                    status = "健康" if host.get('healthy', False) else "不健康"
                    print(f"   实例{i+1}: {host.get('ip')}:{host.get('port')} - {status}")
                return True
            else:
                print(f"❌ 服务 {service_name} 未注册或无实例")
                return False
        else:
            print(f"❌ 查询服务 {service_name} 失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查服务 {service_name} 注册状态失败: {e}")
        return False

def test_service_endpoints():
    """测试微服务端点"""
    services = [
        ('OrderService', 'http://localhost:8001'),
        ('PaymentService', 'http://localhost:8002'),
        ('NotificationService', 'http://localhost:8003')
    ]

    for service_name, endpoint in services:
        try:
            response = requests.get(f"{endpoint}/health/", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} 健康检查通过")
            else:
                print(f"❌ {service_name} 健康检查失败: {response.status_code}")
        except Exception as e:
            print(f"❌ {service_name} 连接失败: {e}")

def main():
    """主函数"""
    print("🔍 开始检查CFMP微服务系统状态...\n")

    # 1. 测试Nacos连接
    print("1. 测试Nacos连接...")
    if not test_nacos_connection():
        print("请确保Nacos服务器正在运行")
        return

    # 2. 获取访问令牌
    print("\n2. 获取Nacos访问令牌...")
    token = get_nacos_token()
    if token:
        print("✅ 成功获取访问令牌")
    else:
        print("⚠️  未能获取访问令牌，将尝试无认证访问")

    # 3. 检查服务注册
    print("\n3. 检查服务注册状态...")
    services = ['OrderService', 'PaymentService', 'NotificationService']
    registered_count = 0

    for service in services:
        if check_service_registration(service, token):
            registered_count += 1

    print(f"\n📊 注册状态汇总: {registered_count}/{len(services)} 服务已注册")

    # 4. 测试服务端点
    print("\n4. 测试微服务端点...")
    test_service_endpoints()

    print("\n✅ 检查完成！")
    if registered_count == len(services):
        print("🎉 所有微服务都已成功注册到Nacos！")
    else:
        print("⚠️  部分服务未注册，请检查服务启动状态")

if __name__ == "__main__":
    main()
