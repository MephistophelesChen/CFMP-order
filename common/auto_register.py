"""
Django应用配置 - 自动服务注册
在每个Django服务的apps.py中使用此配置
"""

import os
import sys
import time
import threading
import logging
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)

class AutoRegisterConfig(AppConfig):
    """自动注册服务配置"""

    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.service_name = os.getenv('SERVICE_NAME', app_name.title() + 'Service')

    def ready(self):
        """Django应用就绪时自动注册服务"""
        # 避免在Django migrate/collectstatic等命令时注册
        if any(cmd in sys.argv for cmd in ['migrate', 'collectstatic', 'makemigrations', 'shell']):
            return

        if 'runserver' in sys.argv:
            # 延迟注册，确保服务完全启动
            threading.Timer(3.0, self._register_service).start()

    def _register_service(self):
        """注册服务到Nacos"""
        try:
            from common.service_registry import service_registry

            # 获取实际端口
            port = self._get_actual_port()
            if port:
                # 设置环境变量供service_registry使用
                os.environ['ACTUAL_SERVICE_PORT'] = str(port)
                service_registry.register_django_service(self.service_name)
                logger.info(f"服务自动注册成功: {self.service_name} (端口: {port})")
            else:
                logger.error("无法获取服务实际端口，注册失败")

        except Exception as e:
            logger.error(f"自动注册服务失败: {e}")

    def _get_actual_port(self):
        """获取Django服务实际使用的端口"""
        try:
            # 方法1: 从环境变量获取
            port = os.getenv('ACTUAL_SERVICE_PORT') or os.getenv('SERVICE_PORT')
            if port:
                return int(port)

            # 方法2: 解析命令行参数
            if 'runserver' in sys.argv:
                runserver_index = sys.argv.index('runserver')
                if runserver_index + 1 < len(sys.argv):
                    arg = sys.argv[runserver_index + 1]
                    if ':' in arg:
                        return int(arg.split(':')[1])
                    elif arg.isdigit():
                        return int(arg)

            # 方法3: 检查Django settings
            if hasattr(settings, 'SERVER_PORT'):
                return settings.SERVER_PORT

            return None

        except (ValueError, IndexError):
            return None
