from django.apps import AppConfig


class OrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order'

    def ready(self):
        """应用启动时的初始化"""
        import os
        import sys
        from pathlib import Path

        # 添加公共模块路径 - 使用与settings.py相同的方式
        BASE_DIR = Path(__file__).resolve().parent.parent
        COMMON_DIR = BASE_DIR.parent / 'common'
        sys.path.insert(0, str(COMMON_DIR))

        try:
            # 使用importlib导入服务注册模块
            import importlib.util
            spec = importlib.util.spec_from_file_location("service_registry", COMMON_DIR / "service_registry.py")
            if spec and spec.loader:
                service_registry = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(service_registry)

                # 注册订单服务到Nacos
                service_registry.register_service('OrderService')
                print("订单服务已注册到Nacos")

        except Exception as e:
            print(f"订单服务注册失败: {e}")
            import traceback
            traceback.print_exc()