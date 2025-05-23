#!/usr/bin/env python3
"""
标准MCP客户端测试工具
使用JSON-RPC 2.0协议与MCP服务器通信
"""

import requests
import json
import time
import logging
import argparse
from typing import Dict, Any, Optional

try:
    import sseclient
except ImportError:
    print("请安装sseclient-py: pip install sseclient-py")
    exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-client")

class JSONRPCError(Exception):
    """JSON-RPC错误"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")

class MCPClient:
    """标准MCP客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.request_id = 1
    
    def send_jsonrpc_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """发送JSON-RPC 2.0请求"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method
        }
        
        if params is not None:
            request["params"] = params
        
        self.request_id += 1
        
        logger.debug(f"发送请求: {method}")
        response = self.session.post(
            f"{self.base_url}/mcp",
            json=request
        )
        response.raise_for_status()
        
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            raise JSONRPCError(
                error["code"],
                error["message"],
                error.get("data")
            )
        
        return result.get("result", {})
    
    def initialize(self) -> Dict[str, Any]:
        """初始化MCP连接"""
        return self.send_jsonrpc_request("initialize", {
            "protocolVersion": "1.0",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-test-client",
                "version": "1.0.0"
            }
        })
    
    def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        return self.send_jsonrpc_request("tools/list")
    
    def list_resources(self) -> Dict[str, Any]:
        """列出可用资源"""
        return self.send_jsonrpc_request("resources/list")
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        return self.send_jsonrpc_request("tools/call", {
            "name": name,
            "arguments": arguments
        })
    
    def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        return self.send_jsonrpc_request("resources/read", {
            "uri": uri
        })
    
    def stream_events(self, stream_id: str, callback=None, timeout: int = 60):
        """监听SSE流"""
        url = f"{self.base_url}/mcp/stream/{stream_id}"
        
        logger.info(f"连接到流: {url}")
        
        try:
            response = self.session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.data.startswith('{'):
                    try:
                        data = json.loads(event.data)
                        logger.info(f"收到流事件: {data.get('type', 'unknown')}")
                        
                        if callback:
                            callback(data)
                        
                        # 如果收到结束信号，退出
                        if data.get("type") == "end":
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"解析SSE数据失败: {e}")
                        
        except Exception as e:
            logger.error(f"流连接错误: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_server_info(self) -> Dict[str, Any]:
        """获取服务器信息"""
        response = self.session.get(f"{self.base_url}/mcp/info")
        response.raise_for_status()
        return response.json()

def test_basic_functionality(client: MCPClient):
    """测试基本功能"""
    print("=== 标准MCP基本功能测试 ===\n")
    
    try:
        # 1. 健康检查
        print("1. 健康检查")
        health = client.health_check()
        print(f"   服务器状态: {health['status']}")
        print(f"   协议: {health.get('protocol', 'Unknown')}")
        print()
        
        # 2. 获取服务器信息
        print("2. 获取服务器信息")
        info = client.get_server_info()
        print(f"   服务器: {info['name']} v{info['version']}")
        print(f"   协议: {info['protocol']['name']} v{info['protocol']['version']}")
        print(f"   端点: {info['endpoint']['url']}")
        print()
        
        # 3. 初始化MCP连接
        print("3. 初始化MCP连接")
        init_result = client.initialize()
        print(f"   协议版本: {init_result['protocolVersion']}")
        print(f"   服务器: {init_result['serverInfo']['name']} v{init_result['serverInfo']['version']}")
        print()
        
        # 4. 列出工具
        print("4. 列出可用工具")
        tools = client.list_tools()
        for tool in tools['tools']:
            print(f"   - {tool['name']}: {tool['description']}")
        print()
        
        # 5. 列出资源
        print("5. 列出可用资源")
        resources = client.list_resources()
        for resource in resources['resources']:
            print(f"   - {resource['uri']}: {resource['name']}")
        print()
        
        # 6. 获取模型
        print("6. 获取可用模型")
        models_result = client.call_tool("get_models", {})
        models_data = json.loads(models_result['content'][0]['text'])
        for model in models_data['models']:
            print(f"   - {model['name']}: {model['description']}")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"基本功能测试失败: {e}")
        return False

def test_audio_separation(client: MCPClient, test_file: str = "/tmp/test_audio.mp3"):
    """测试音频分离功能"""
    print("=== 音频分离测试 ===\n")
    
    import os
    
    # 创建测试文件
    if not os.path.exists(test_file):
        print(f"创建测试文件: {test_file}")
        with open(test_file, 'w') as f:
            f.write("fake audio content")
    
    try:
        print("1. 开始音频分离任务")
        
        # 调用音频分离工具
        result = client.call_tool("separate_audio", {
            "file_path": test_file,
            "model": "htdemucs",
            "stems": ["vocals", "drums"],
            "stream_progress": True
        })
        
        task_info = json.loads(result['content'][0]['text'])
        job_id = task_info['job_id']
        
        print(f"   任务ID: {job_id}")
        print(f"   状态: {task_info['status']}")
        print()
        
        if task_info.get('stream_url'):
            print("2. 监听进度流")
            
            def progress_callback(data):
                if data.get("type") == "progress":
                    print(f"   进度: {data['progress']}% - {data['message']}")
                elif data.get("type") == "completed":
                    print(f"   ✅ 完成: {data['message']}")
                elif data.get("type") == "error":
                    print(f"   ❌ 错误: {data['message']}")
            
            # 从stream_url提取stream_id
            stream_id = task_info['stream_url'].split('/')[-1]
            client.stream_events(stream_id, progress_callback)
            
            print()
        
        return True
        
    except Exception as e:
        logger.error(f"音频分离测试失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="标准MCP客户端测试工具")
    parser.add_argument("--url", default="http://localhost:8080", help="MCP服务器URL")
    parser.add_argument("--test", choices=["basic", "audio", "all"], default="all", help="测试类型")
    
    args = parser.parse_args()
    
    client = MCPClient(args.url)
    
    print(f"连接到标准MCP服务器: {args.url}")
    print("使用JSON-RPC 2.0协议")
    print("=" * 50)
    
    success = True
    
    if args.test in ["basic", "all"]:
        success &= test_basic_functionality(client)
    
    if args.test in ["audio", "all"]:
        success &= test_audio_separation(client)
    
    if success:
        print("🎉 所有测试通过!")
    else:
        print("❌ 测试失败")
        exit(1)

if __name__ == "__main__":
    main() 