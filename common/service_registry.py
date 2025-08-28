"""
Django服务注册模块
用于在Django应用启动时自动注册到Nacos
"""
import os
import sys
import logging
import atexit
import socket

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
        # 1. 从实际端口环境变量获取（优先级最高）
        actual_port = os.getenv('ACTUAL_SERVICE_PORT')
        if actual_port:
            return int(actual_port)

        # 2. 从环境变量获取
        port = os.getenv('SERVICE_PORT')
        if port:
            return int(port)

        # 3. 从Django runserver命令行参数获取
        port = self._parse_runserver_port()
        if port:
            # 检查端口是否可用，如果不可用则自动分配
            if self._is_port_available(port):
                return port
            else:
                logger.warning(f"指定端口 {port} 不可用，尝试自动分配端口")
                return self._get_available_port(port)

        # 4. 自动分配可用端口（从8000开始）
        return self._get_available_port(8000)

    def _get_available_port(self, start_port=8000):
        """获取可用端口"""
        for port in range(start_port, start_port + 100):
            if self._is_port_available(port):
                logger.info(f"自动分配端口: {port}")
                return port
        raise Exception(f"无法找到可用端口 (尝试范围: {start_port}-{start_port + 99})")

    def _is_port_available(self, port):
        """检查端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False

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
