"""
标准MCP (Model Context Protocol) 服务实现
基于JSON-RPC 2.0协议的单一端点通信
"""

import uuid
import time
import json
import logging
import threading
import queue
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from flask import current_app

logger = logging.getLogger(__name__)

class MCPVersion(str, Enum):
    """MCP协议版本"""
    V1_0 = "1.0"

@dataclass
class JSONRPCRequest:
    """JSON-RPC请求"""
    jsonrpc: str
    method: str
    id: Optional[Union[str, int]] = None
    params: Optional[Dict[str, Any]] = None

@dataclass
class JSONRPCResponse:
    """JSON-RPC响应"""
    jsonrpc: str
    id: Optional[Union[str, int]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

@dataclass
class JSONRPCNotification:
    """JSON-RPC通知"""
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None

class MCPServer:
    """标准MCP服务器实现"""
    
    def __init__(self, name: str = "demucs-audio-separator", version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.streams: Dict[str, queue.Queue] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.app = None
        
        # 服务器能力
        self.capabilities = {
            "tools": {
                "listChanged": False
            },
            "resources": {
                "subscribe": True,
                "listChanged": False  
            },
            "experimental": {
                "streaming": True
            }
        }
        
        # 可用工具
        self.tools = [
            {
                "name": "separate_audio",
                "description": "使用Demucs模型分离音频文件为不同音轨（人声、鼓点、贝斯等）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "要处理的音频文件路径"
                        },
                        "model": {
                            "type": "string",
                            "enum": ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_q"],
                            "default": "htdemucs",
                            "description": "使用的Demucs模型"
                        },
                        "stems": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["vocals", "drums", "bass", "other", "piano", "guitar"]
                            },
                            "description": "要分离的音轨类型"
                        },
                        "stream_progress": {
                            "type": "boolean",
                            "default": True,
                            "description": "是否启用流式进度输出"
                        }
                    },
                    "required": ["file_path"]
                }
            },
            {
                "name": "get_models",
                "description": "获取可用的Demucs音频分离模型列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "get_job_status",
                "description": "获取音频分离任务的当前状态",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "任务ID"
                        }
                    },
                    "required": ["job_id"]
                }
            }
        ]
        
        # 可用资源
        self.resources = [
            {
                "uri": "demucs://docs/api",
                "name": "API Documentation",
                "description": "Demucs音频分离服务的API文档",
                "mimeType": "text/markdown"
            },
            {
                "uri": "demucs://models/info",
                "name": "Models Information", 
                "description": "可用音频分离模型的详细信息",
                "mimeType": "application/json"
            }
        ]
    
    def set_app(self, app):
        """设置Flask应用实例"""
        self.app = app
    
    def handle_jsonrpc_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理JSON-RPC请求"""
        try:
            # 验证JSON-RPC格式
            if request_data.get("jsonrpc") != "2.0":
                return self._create_error_response(
                    None, -32600, "Invalid Request", "Invalid JSON-RPC version"
                )
            
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            if not method:
                return self._create_error_response(
                    request_id, -32600, "Invalid Request", "Missing method"
                )
            
            # 路由到对应的处理方法
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "tools/list":
                result = self._handle_tools_list(params)
            elif method == "tools/call":
                result = self._handle_tools_call(params)
            elif method == "resources/list":
                result = self._handle_resources_list(params)
            elif method == "resources/read":
                result = self._handle_resources_read(params)
            else:
                return self._create_error_response(
                    request_id, -32601, "Method not found", f"Unknown method: {method}"
                )
            
            return self._create_success_response(request_id, result)
            
        except Exception as e:
            logger.error(f"处理JSON-RPC请求时出错: {str(e)}")
            return self._create_error_response(
                request_data.get("id"), -32603, "Internal error", str(e)
            )
    
    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "protocolVersion": MCPVersion.V1_0,
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具列表请求"""
        return {"tools": self.tools}
    
    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise ValueError("Tool name is required")
        
        if tool_name == "get_models":
            return self._get_models()
        elif tool_name == "get_job_status":
            return self._get_job_status(arguments)
        elif tool_name == "separate_audio":
            return self._separate_audio(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源列表请求"""
        return {"resources": self.resources}
    
    def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源读取请求"""
        uri = params.get("uri")
        
        if not uri:
            raise ValueError("Resource URI is required")
        
        return self._read_resource(uri)
    
    def _get_models(self) -> Dict[str, Any]:
        """获取模型列表"""
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "models": [
                        {
                            "name": "htdemucs",
                            "description": "Hybrid Transformer Demucs - 默认高质量模型",
                            "stems": ["vocals", "drums", "bass", "other"]
                        },
                        {
                            "name": "htdemucs_ft",
                            "description": "Fine-tuned Hybrid Transformer Demucs - 更高质量",
                            "stems": ["vocals", "drums", "bass", "other"]
                        },
                        {
                            "name": "htdemucs_6s",
                            "description": "6-stem Hybrid Transformer Demucs - 包含钢琴和吉他",
                            "stems": ["vocals", "drums", "bass", "other", "piano", "guitar"]
                        },
                        {
                            "name": "mdx",
                            "description": "MDX模型 - 平衡型",
                            "stems": ["vocals", "drums", "bass", "other"]
                        },
                        {
                            "name": "mdx_q",
                            "description": "MDX量化模型 - 快速处理",
                            "stems": ["vocals", "drums", "bass", "other"]
                        }
                    ]
                }, indent=2)
            }]
        }
    
    def _get_job_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取任务状态"""
        job_id = arguments.get("job_id")
        
        with self.lock:
            if job_id in self.jobs:
                job_info = self.jobs[job_id]
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(job_info, indent=2)
                    }]
                }
            else:
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "error": f"Job {job_id} not found"
                        }, indent=2)
                    }]
                }
    
    def _separate_audio(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行音频分离"""
        import os
        
        file_path = arguments.get("file_path")
        model = arguments.get("model", "htdemucs")
        stems = arguments.get("stems", ["vocals", "drums", "bass", "other"])
        stream_progress = arguments.get("stream_progress", True)
        
        # 验证文件路径
        if not os.path.exists(file_path):
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "error": f"File not found: {file_path}"
                    }, indent=2)
                }]
            }
        
        # 生成任务ID
        job_id = str(uuid.uuid4())
        
        # 初始化任务信息
        job_info = {
            "job_id": job_id,
            "status": "started",
            "file_path": file_path,
            "model": model,
            "stems": stems,
            "progress": 0,
            "message": "任务已创建",
            "stream_url": f"/mcp/stream/{job_id}" if stream_progress else None,
            "created_at": time.time()
        }
        
        with self.lock:
            self.jobs[job_id] = job_info
        
        # 如果启用流式输出，启动处理线程
        if stream_progress:
            threading.Thread(
                target=self._simulate_audio_processing_with_context,
                args=(job_id, file_path, model, stems),
                daemon=True
            ).start()
        
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "job_id": job_id,
                    "status": "started",
                    "message": "音频分离任务已开始",
                    "stream_url": f"/mcp/stream/{job_id}" if stream_progress else None,
                    "model": model,
                    "stems": stems
                }, indent=2)
            }]
        }
    
    def _read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源内容"""
        
        if uri == "demucs://docs/api":
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": """# Demucs Audio Separation MCP Server

## 概述
Demucs音频分离MCP服务器提供基于深度学习的音频源分离功能，通过标准MCP协议进行通信。

## 可用工具

### separate_audio
使用Demucs模型分离音频文件
- **file_path**: 音频文件路径
- **model**: 使用的模型 (htdemucs, htdemucs_ft, htdemucs_6s, mdx, mdx_q)
- **stems**: 要分离的音轨类型数组
- **stream_progress**: 是否启用流式进度输出

### get_models
获取可用的Demucs模型列表

### get_job_status
获取音频分离任务的状态
- **job_id**: 任务ID

## 流式输出
当启用stream_progress时，可以通过SSE端点 `/mcp/stream/{job_id}` 获取实时进度更新。

## JSON-RPC 2.0 协议
所有通信均通过单一端点 `/mcp` 进行，使用标准JSON-RPC 2.0消息格式。
"""
                }]
            }
        
        elif uri == "demucs://models/info":
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "models": [
                            {
                                "name": "htdemucs",
                                "description": "Hybrid Transformer Demucs",
                                "architecture": "hybrid transformer",
                                "quality": "high",
                                "speed": "medium",
                                "stems": ["vocals", "drums", "bass", "other"],
                                "recommended": True
                            },
                            {
                                "name": "htdemucs_ft",
                                "description": "Fine-tuned Hybrid Transformer Demucs",
                                "architecture": "hybrid transformer",
                                "quality": "highest",
                                "speed": "slow",
                                "stems": ["vocals", "drums", "bass", "other"],
                                "recommended": False
                            },
                            {
                                "name": "htdemucs_6s",
                                "description": "6-stem Hybrid Transformer Demucs",
                                "architecture": "hybrid transformer",
                                "quality": "high",
                                "speed": "medium",
                                "stems": ["vocals", "drums", "bass", "other", "piano", "guitar"],
                                "recommended": False
                            },
                            {
                                "name": "mdx",
                                "description": "MDX model",
                                "architecture": "mdx",
                                "quality": "medium",
                                "speed": "fast",
                                "stems": ["vocals", "drums", "bass", "other"],
                                "recommended": False
                            },
                            {
                                "name": "mdx_q",
                                "description": "Quantized MDX model",
                                "architecture": "mdx",
                                "quality": "medium",
                                "speed": "fastest",
                                "stems": ["vocals", "drums", "bass", "other"],
                                "recommended": False
                            }
                        ]
                    }, indent=2)
                }]
            }
        
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    def _simulate_audio_processing_with_context(self, job_id: str, file_path: str, model: str, stems: List[str]):
        """带应用上下文的音频处理"""
        if self.app:
            with self.app.app_context():
                self._simulate_audio_processing(job_id, file_path, model, stems)
        else:
            self._simulate_audio_processing(job_id, file_path, model, stems)
    
    def _simulate_audio_processing(self, job_id: str, file_path: str, model: str, stems: List[str]):
        """模拟音频处理过程"""
        
        try:
            # 更新任务状态为处理中
            with self.lock:
                if job_id in self.jobs:
                    self.jobs[job_id].update({
                        "status": "processing",
                        "message": "正在初始化音频处理"
                    })
            
            # 发送初始进度
            self.send_to_stream(job_id, {
                "type": "progress",
                "job_id": job_id,
                "progress": 0,
                "status": "processing",
                "message": "正在加载模型..."
            })
            
            # 模拟处理进度
            for i in range(1, 101):
                time.sleep(0.1)  # 模拟处理时间
                
                # 生成进度消息
                if i < 20:
                    message = f"正在加载 {model} 模型..."
                elif i < 40:
                    message = "正在分析音频频谱..."
                elif i < 80:
                    message = f"正在分离音轨 ({', '.join(stems)})..."
                else:
                    message = "正在保存结果文件..."
                
                # 更新任务状态
                with self.lock:
                    if job_id in self.jobs:
                        self.jobs[job_id].update({
                            "progress": i,
                            "message": message
                        })
                
                # 发送进度更新
                self.send_to_stream(job_id, {
                    "type": "progress",
                    "job_id": job_id,
                    "progress": i,
                    "status": "processing",
                    "message": message
                })
            
            # 处理完成
            output_files = [f"{file_path.rsplit('.', 1)[0]}_{stem}.wav" for stem in stems]
            
            with self.lock:
                if job_id in self.jobs:
                    self.jobs[job_id].update({
                        "status": "completed",
                        "progress": 100,
                        "message": "音频分离完成",
                        "output_files": output_files,
                        "completed_at": time.time()
                    })
            
            # 发送完成通知
            self.send_to_stream(job_id, {
                "type": "completed",
                "job_id": job_id,
                "progress": 100,
                "status": "completed",
                "message": "音频分离完成",
                "output_files": output_files
            })
            
            # 发送结束信号
            self.send_to_stream(job_id, {
                "type": "end",
                "job_id": job_id
            })
            
        except Exception as e:
            logger.error(f"处理任务 {job_id} 时出错: {str(e)}")
            
            # 更新错误状态
            with self.lock:
                if job_id in self.jobs:
                    self.jobs[job_id].update({
                        "status": "error",
                        "message": f"处理出错: {str(e)}",
                        "error_at": time.time()
                    })
            
            # 发送错误通知
            self.send_to_stream(job_id, {
                "type": "error",
                "job_id": job_id,
                "status": "error",
                "message": f"处理出错: {str(e)}"
            })
            
            # 发送结束信号
            self.send_to_stream(job_id, {
                "type": "end",
                "job_id": job_id
            })
    
    def create_stream(self, stream_id: str) -> queue.Queue:
        """创建一个新的流"""
        with self.lock:
            stream_queue = queue.Queue()
            self.streams[stream_id] = stream_queue
            logger.info(f"创建MCP流: {stream_id}")
            return stream_queue
    
    def close_stream(self, stream_id: str):
        """关闭流"""
        with self.lock:
            if stream_id in self.streams:
                del self.streams[stream_id]
                logger.info(f"关闭MCP流: {stream_id}")
    
    def send_to_stream(self, stream_id: str, data: Dict[str, Any]):
        """向流发送数据"""
        with self.lock:
            if stream_id in self.streams:
                self.streams[stream_id].put(data)
                logger.debug(f"发送到MCP流 {stream_id}: {data}")
    
    def generate_stream_events(self, stream_id: str):
        """生成SSE流事件"""
        stream_queue = self.create_stream(stream_id)
        
        try:
            while True:
                try:
                    # 等待流数据
                    data = stream_queue.get(timeout=30)
                    
                    # 格式化为SSE格式
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    # 如果是结束信号，退出循环
                    if data.get("type") == "end":
                        break
                        
                except queue.Empty:
                    # 发送心跳
                    yield f": heartbeat {time.time()}\n\n"
                    
        except GeneratorExit:
            logger.info(f"MCP客户端断开连接: {stream_id}")
        finally:
            self.close_stream(stream_id)
    
    def _create_success_response(self, request_id: Optional[Union[str, int]], result: Dict[str, Any]) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    
    def _create_error_response(self, request_id: Optional[Union[str, int]], code: int, message: str, data: Optional[str] = None) -> Dict[str, Any]:
        """创建错误响应"""
        error = {
            "code": code,
            "message": message
        }
        if data:
            error["data"] = data
            
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        } 