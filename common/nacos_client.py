"""
Nacos服务注册与发现客户端
"""
import nacos
import os
import logging
import threading
import time
import socket
import sys
import random

logger = logging.getLogger(__name__)

class NacosClient:
    """Nacos客户端封装"""

    def __init__(self):
        # 从环境变量获取Nacos服务器配置
        self.server_addresses = os.getenv('NACOS_SERVER', '127.0.0.1:8848')
        self.namespace = os.getenv('NACOS_NAMESPACE', 'public')
        self.username = os.getenv('NACOS_USERNAME', 'nacos')
        self.password = os.getenv('NACOS_PASSWORD', 'nacos')
        self.group_name = os.getenv('NACOS_GROUP', 'DEFAULT_GROUP')

        # 获取本机IP，优先使用环境变量，否则自动检测
        self.local_ip = os.getenv('NODE_IP', self._get_local_ip())        # 心跳线程控制
        self._heartbeat_threads = {}
        self._stop_heartbeat = {}

        try:
            self.client = nacos.NacosClient(
                server_addresses=self.server_addresses,
                namespace=self.namespace,
                username=self.username,
                password=self.password
            )
            logger.info(f"Nacos客户端初始化成功: {self.server_addresses}")
        except Exception as e:
            logger.error(f"Nacos客户端初始化失败: {e}")
            self.client = None

    def _get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个socket连接来获取本机IP
            return os.getenv("NODE_IP", "101.200.231.225")
        except Exception:
            return "127.0.0.1"

    def register_service(self, service_name, port=None, metadata=None):
        """注册服务并启动心跳"""
        if not self.client:
            logger.error("Nacos客户端未初始化")
            return False

        # 如果没有传入端口，从环境变量获取
        if port is None:
            port = int(os.getenv("NODE_PORT", random.randint(30000, 32767)))

        try:
            # 注册服务实例
            result = self.client.add_naming_instance(
                service_name=service_name,
                ip=self.local_ip,
                port=port,
                cluster_name="DEFAULT",
                healthy=True,
                metadata=metadata or {}
            )

            if result:
                logger.info(f"服务注册成功: {service_name}@{self.local_ip}:{port}")
                # 启动心跳线程
                self._start_heartbeat(service_name, port)
                return True
            else:
                logger.error(f"服务注册失败: {service_name}")
                return False
        except Exception as e:
            logger.error(f"服务注册失败: {e}")
            return False

    def _start_heartbeat(self, service_name, port):
        """启动心跳线程"""
        if service_name in self._heartbeat_threads:
            logger.warning(f"心跳线程已存在: {service_name}")
            return

        self._stop_heartbeat[service_name] = False
        thread = threading.Thread(
            target=self._send_heartbeat,
            args=(service_name, port),
            daemon=True
        )
        thread.start()
        self._heartbeat_threads[service_name] = thread
        logger.info(f"心跳线程已启动: {service_name}")

    def _send_heartbeat(self, service_name, port):
        """发送心跳"""
        while not self._stop_heartbeat.get(service_name, True):
            try:
                if self.client:
                    # 通过重新注册实例来维持心跳
                    # 这是因为nacos-sdk-python可能没有专门的心跳方法
                    self.client.add_naming_instance(
                        service_name=service_name,
                        ip=self.local_ip,
                        port=port,
                        cluster_name="DEFAULT",
                        healthy=True
                    )
                    logger.debug(f"心跳发送成功: {service_name}")
                else:
                    logger.error("Nacos客户端未初始化，无法发送心跳")
                time.sleep(5)  # 每5秒发送一次心跳
            except Exception as e:
                logger.error(f"心跳发送失败 {service_name}: {e}")
                time.sleep(5)

    def discover_service(self, service_name):
        """发现服务"""
        if not self.client:
            logger.error("Nacos客户端未初始化")
            return []

        try:
            response = self.client.list_naming_instance(
                service_name=service_name,
                group_name=self.group_name
            )

            # 检查响应类型并解析
            if isinstance(response, str):
                import json
                response = json.loads(response)

            # 从响应中提取hosts数组
            instances = response.get('hosts', []) if isinstance(response, dict) else []
            healthy_instances = [instance for instance in instances if instance.get('healthy', False)]
            logger.info(f"发现服务实例: {service_name} - {len(healthy_instances)}个健康实例")
            return healthy_instances
        except Exception as e:
            logger.error(f"服务发现失败: {e}")
            return []

    def deregister_service(self, service_name, port=None):
        """注销服务并停止心跳"""
        if not self.client:
            logger.error("Nacos客户端未初始化")
            return False

        # 如果没有传入端口，从环境变量获取
        if port is None:
            port = int(os.getenv("NODE_PORT", 30000))

        try:
            # 停止心跳
            self._stop_heartbeat[service_name] = True
            if service_name in self._heartbeat_threads:
                del self._heartbeat_threads[service_name]

            # 注销服务实例
            result = self.client.remove_naming_instance(
                service_name=service_name,
                ip=self.local_ip,
                port=port,
                cluster_name="DEFAULT"
            )
            logger.info(f"服务注销成功: {service_name}@{self.local_ip}:{port}")
            return result
        except Exception as e:
            logger.error(f"服务注销失败: {e}")
            return False

    def get_service_port_from_args(self, default=8000):
        """从命令行参数获取端口号"""
        for arg in sys.argv:
            if ":" in arg:
                try:
                    return int(arg.split(":")[1])
                except ValueError:
                    pass
            elif arg.isdigit():
                return int(arg)
        return default

# 全局Nacos客户端实例
nacos_client = NacosClient()
