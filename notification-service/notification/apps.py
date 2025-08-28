from django.apps import AppConfig
import os
import sys
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notification'

    def ready(self):
        """应用启动时的初始化"""
        # 避免在Django migrate/collectstatic等命令时注册
        if any(cmd in sys.argv for cmd in ['migrate', 'collectstatic', 'makemigrations', 'shell']):
            return

        if 'runserver' in sys.argv:
            # 延迟注册，确保服务完全启动并获取到实际端口
            threading.Timer(3.0, self._register_service).start()

    def _register_service(self):
        """注册服务到Nacos"""
        try:
            # 添加公共模块路径
            BASE_DIR = Path(__file__).resolve().parent.parent
            # 在容器中，common模块与notification-service在同一级目录
            COMMON_DIR = BASE_DIR / 'common'
            sys.path.insert(0, str(COMMON_DIR))

            # 获取实际端口
            port = self._get_actual_port()
            if port:
                # 设置环境变量供service_registry使用
                os.environ['ACTUAL_SERVICE_PORT'] = str(port)
                logger.info(f"通知服务实际端口: {port}")

            # 使用importlib导入服务注册模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("service_registry", COMMON_DIR / "service_registry.py")
            if spec and spec.loader:
                service_registry = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(service_registry)

                # 注册通知服务到Nacos
                service_registry.register_service('NotificationService')
                logger.info("通知服务已注册到Nacos")

        except Exception as e:
            logger.error(f"通知服务注册失败: {e}")
            import traceback
            traceback.print_exc()

    def _get_actual_port(self):
        """获取Django服务实际使用的端口"""
        try:
            # 从环境变量获取
            port = os.getenv('SERVICE_PORT')
            if port:
                return int(port)

            # 解析命令行参数
            if 'runserver' in sys.argv:
                runserver_index = sys.argv.index('runserver')
                if runserver_index + 1 < len(sys.argv):
                    arg = sys.argv[runserver_index + 1]
                    if ':' in arg:
                        return int(arg.split(':')[1])
                    elif arg.isdigit():
                        return int(arg)

            return None

        except (ValueError, IndexError):
            return None

        except Exception as e:
            print(f"通知服务注册失败: {e}")
            import traceback
            traceback.print_exc()