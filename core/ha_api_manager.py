import requests
import json
from typing import Dict, Any, Optional

class HAAPIManager:
    """Home Assistant API管理器"""
    
    def __init__(self, base_url: str = "", token: str = ""):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.timeout = 5  # 5秒超时
    
    def update_config(self, base_url: str, token: str):
        """更新配置"""
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
    
    def test_connection(self) -> tuple[bool, str]:
        """测试HA连接"""
        try:
            url = f"{self.base_url}/api/"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return True, f"连接成功 - {data.get('message', 'OK')}"
            else:
                return False, f"连接失败: HTTP {response.status_code}"
        except requests.exceptions.Timeout:
            return False, "连接超时"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到Home Assistant"
        except Exception as e:
            return False, f"错误: {str(e)}"
    
    def call_service(self, service_path: str, data: Dict[str, Any], 
                    custom_headers: Optional[Dict[str, str]] = None) -> tuple[bool, str]:
        """
        调用HA服务
        
        Args:
            service_path: 服务路径，如 '/api/services/xiaomi_miot/intelligent_speaker'
            data: 请求体数据
            custom_headers: 自定义headers（可选）
            
        Returns:
            (成功标志, 响应消息)
        """
        try:
            url = f"{self.base_url}{service_path}"
            
            # 合并headers
            headers = self.headers.copy()
            if custom_headers:
                headers.update(custom_headers)
            
            print(f"[HA API] POST {url}")
            print(f"[HA API] Data: {json.dumps(data, ensure_ascii=False)}")
            
            response = requests.post(
                url, 
                json=data, 
                headers=headers, 
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                return True, "调用成功"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
                
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, "连接失败"
        except Exception as e:
            return False, f"错误: {str(e)}"
    
    def replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        替换模板中的变量
        
        Args:
            template: 模板字符串，如 "第{count}次{exercise}"
            variables: 变量字典，如 {"count": 5, "exercise": "深蹲"}
            
        Returns:
            替换后的字符串
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def prepare_body_with_variables(self, body_params: list, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备请求体，替换变量
        
        Args:
            body_params: 参数列表
            variables: 变量字典
            
        Returns:
            处理后的请求体字典
        """
        body = {}
        for param in body_params:
            if not param.get('enabled', True):
                continue
            
            key = param['key']
            value = param['value']
            param_type = param.get('type', 'string')
            use_variables = param.get('use_variables', False)
            
            # 字符串类型且需要替换变量
            if param_type == 'string' and use_variables and isinstance(value, str):
                value = self.replace_variables(value, variables)
            
            body[key] = value
        
        return body
