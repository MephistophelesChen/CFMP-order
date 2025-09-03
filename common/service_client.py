"""
微服务间HTTP通信客户端
"""
import requests
import logging
import json
from typing import Dict, List, Optional, Any

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

class ServiceClient:
    """服务间通信客户端"""

    def __init__(self, timeout=30):
        self.timeout = timeout
        self.session = requests.Session()
        # 设置公共请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def get_service_url(self, service_name: str) -> Optional[str]:
        """获取服务URL"""
        instances = nacos_client.discover_service(service_name)
        if not instances:
            logger.error(f"未发现服务实例: {service_name}")
            return None

        # 简单的负载均衡：选择第一个健康实例
        instance = instances[0]
        return f"http://{instance['ip']}:{instance['port']}"

    def request(self, service_name: str, method: str, path: str,
                data: Optional[Dict] = None, params: Optional[Dict] = None,
                headers: Optional[Dict] = None) -> Optional[Dict]:
        """发送HTTP请求"""
        base_url = self.get_service_url(service_name)
        if not base_url:
            logger.error(f"无法获取服务URL: {service_name}")
            return None

        url = f"{base_url}{path}"
        logger.info(f"发起HTTP请求: {method} {url}")
        if data:
            logger.info(f"请求数据: {data}")

        try:
            request_headers = dict(self.session.headers)
            if headers:
                request_headers.update(headers)

            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.timeout
            )

            logger.info(f"HTTP响应状态: {response.status_code}")
            logger.info(f"HTTP响应内容: {response.text[:500]}...")

            response.raise_for_status()

            if response.content:
                result = response.json()
                logger.info(f"解析后的响应: {result}")
                return result
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"服务请求失败: {method} {url} - {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"错误响应内容: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"响应解析失败: {e}")
            return None

    def get(self, service_name: str, path: str, params: Optional[Dict] = None,
            headers: Optional[Dict] = None) -> Optional[Dict]:
        """GET请求"""
        return self.request(service_name, 'GET', path, params=params, headers=headers)

    def post(self, service_name: str, path: str, data: Optional[Dict] = None,
             headers: Optional[Dict] = None) -> Optional[Dict]:
        """POST请求"""
        return self.request(service_name, 'POST', path, data=data, headers=headers)

    def put(self, service_name: str, path: str, data: Optional[Dict] = None,
            headers: Optional[Dict] = None) -> Optional[Dict]:
        """PUT请求"""
        return self.request(service_name, 'PUT', path, data=data, headers=headers)

    def delete(self, service_name: str, path: str, headers: Optional[Dict] = None) -> Optional[Dict]:
        """DELETE请求"""
        return self.request(service_name, 'DELETE', path, headers=headers)

    def patch(self, service_name: str, path: str, data: Optional[Dict] = None,
              headers: Optional[Dict] = None) -> Optional[Dict]:
        """PATCH请求"""
        return self.request(service_name, 'PATCH', path, data=data, headers=headers)

# 全局服务客户端实例
service_client = ServiceClient()
