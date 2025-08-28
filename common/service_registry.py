"""
Django服务注册模块
用于在Django应用启动时自动注册到Nacos
"""
import os
import sys
import logging
import atexit

# 使用绝对导入而不是相对导入
import importlib.util
from pathlib import Path

# 动态导入nacos_client
current_dir = Path(__file__).parent
nacos_client_path = current_dir / "nacos_client.py"
spec = importlib.util.spec_from_file_location("nacos_client", nacos_client_path)
if spec and spec.loader:
    nacos_client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(nacos_client_module)
    nacos_client = nacos_client_module.nacos_client

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """服务注册管理器"""

    def __init__(self):
        self.registered_services = []

    def register_django_service(self, service_name):
        """注册Django服务"""
        try:
            # 从环境变量或命令行参数获取端口
            port = self._get_service_port()

            # 注册服务
            success = nacos_client.register_service(
                service_name=service_name,
                port=port,
                metadata={
                    'framework': 'django',
                    'version': '1.0.0',
                    'environment': os.getenv('ENVIRONMENT', 'development')
                }
            )

            if success:
                self.registered_services.append((service_name, port))
                logger.info(f"Django服务已注册: {service_name} on port {port}")

                # 注册退出时的清理函数
                atexit.register(self._cleanup_on_exit)
            else:
                logger.error(f"Django服务注册失败: {service_name}")

        except Exception as e:
            logger.error(f"注册Django服务时发生错误: {e}")

    def _get_service_port(self):
        """获取服务端口"""
        # 1. 从环境变量获取
        port = os.getenv('SERVICE_PORT')
        if port:
            return int(port)

        # 2. 从Django runserver命令行参数获取
        port = self._parse_runserver_port()
        if port:
            return port

        # 3. 默认端口
        return 8000

    def _parse_runserver_port(self):
        """解析Django runserver命令的端口参数"""
        try:
            # 查找runserver命令后的参数
            if 'runserver' in sys.argv:
                runserver_index = sys.argv.index('runserver')
                if runserver_index + 1 < len(sys.argv):
                    arg = sys.argv[runserver_index + 1]
                    # 处理 host:port 格式
                    if ':' in arg:
                        return int(arg.split(':')[1])
                    # 处理纯端口号格式
                    elif arg.isdigit():
                        return int(arg)
        except (ValueError, IndexError):
            pass
        return None

    def _cleanup_on_exit(self):
        """程序退出时清理注册的服务"""
        for service_name, port in self.registered_services:
            try:
                nacos_client.deregister_service(service_name, port)
                logger.info(f"服务已注销: {service_name}")
            except Exception as e:
                logger.error(f"注销服务失败 {service_name}: {e}")

# 全局服务注册器实例
service_registry = ServiceRegistry()

def register_service(service_name):
    """便捷的服务注册函数"""
    service_registry.register_django_service(service_name)
