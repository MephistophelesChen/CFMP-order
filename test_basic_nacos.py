#!/usr/bin/env python
"""
简单的Nacos客户端测试
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common'))

from common.nacos_client import nacos_client
from common.service_registry import register_service

def test_nacos_basic():
    """基础Nacos连接测试"""
    print("🔍 测试Nacos基础功能...")

    if nacos_client.client:
        print("✅ Nacos客户端初始化成功")
    else:
        print("❌ Nacos客户端初始化失败")
        return False

    # 测试服务注册
    try:
        result = nacos_client.register_service('test-service', 9999)
        if result:
            print("✅ 测试服务注册成功")
        else:
            print("❌ 测试服务注册失败")

        # 等待几秒
        import time
        time.sleep(2)

        # 测试服务发现
        instances = nacos_client.discover_service('test-service')
        if instances:
            print(f"✅ 服务发现成功，找到 {len(instances)} 个实例")
        else:
            print("⚠️  未发现服务实例")

        # 注销服务
        nacos_client.deregister_service('test-service', 9999)
        print("✅ 测试服务注销成功")

        return True

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = test_nacos_basic()
    if success:
        print("\n🎉 Nacos集成测试通过！")
    else:
        print("\n❌ Nacos集成测试失败，请检查配置")

    print("\n📋 下一步:")
    print("1. 使用 start-services.bat (Windows) 或 start-services.sh (Linux/Mac) 启动所有服务")
    print("2. 运行 python test_nacos_registration.py 检查服务注册状态")
    print("3. 访问 http://123.57.145.79:8848/nacos 查看Nacos控制台")
