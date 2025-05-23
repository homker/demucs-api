"""
标准MCP (Model Context Protocol) 路由
基于JSON-RPC 2.0协议的单一端点通信和SSE流式输出
"""

from flask import Blueprint, request, Response, jsonify, current_app
import json
import logging

logger = logging.getLogger(__name__)

mcp_bp = Blueprint('mcp', __name__, url_prefix='/mcp')

@mcp_bp.route('', methods=['POST'])
def mcp_endpoint():
    """
    标准MCP JSON-RPC 2.0端点
    所有MCP通信都通过此单一端点进行
    """
    try:
        # 获取请求数据
        request_data = request.json
        
        if not request_data:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": "Invalid JSON"
                }
            }), 400
        
        # 处理批量请求
        if isinstance(request_data, list):
            responses = []
            for req in request_data:
                response = current_app.mcp_server.handle_jsonrpc_request(req)
                if response:  # 过滤掉通知（无需响应）
                    responses.append(response)
            return jsonify(responses) if responses else ('', 204)
        
        # 处理单个请求
        response = current_app.mcp_server.handle_jsonrpc_request(request_data)
        
        # 如果是通知（没有id），不返回响应
        if request_data.get("id") is None:
            return ('', 204)
        
        return jsonify(response)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error",
                "data": str(e)
            }
        }), 400
    except Exception as e:
        logger.error(f"MCP端点处理错误: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }), 500

@mcp_bp.route('/stream/<stream_id>', methods=['GET'])
def stream_events(stream_id: str):
    """
    SSE流端点，用于流式进度更新
    这是MCP协议的扩展，支持实时进度推送
    """
    try:
        # 获取应用实例和MCP服务
        app = current_app._get_current_object()
        mcp_server = app.mcp_server
        
        def event_generator():
            try:
                with app.app_context():
                    for event in mcp_server.generate_stream_events(stream_id):
                        yield event
            except Exception as e:
                logger.error(f"SSE流生成错误: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return Response(
            event_generator(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
    except Exception as e:
        logger.error(f"创建SSE流时出错: {str(e)}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Failed to create stream: {str(e)}"
            }
        }), 500

@mcp_bp.route('/health', methods=['GET'])
def mcp_health():
    """MCP服务健康检查"""
    try:
        return jsonify({
            "status": "healthy",
            "service": "mcp",
            "protocol": "JSON-RPC 2.0",
            "server": current_app.mcp_server.name,
            "version": current_app.mcp_server.version,
            "active_streams": len(current_app.mcp_server.streams),
            "active_jobs": len(current_app.mcp_server.jobs),
            "endpoint": "/mcp"
        })
    except Exception as e:
        logger.error(f"MCP健康检查失败: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@mcp_bp.route('/info', methods=['GET'])
def mcp_info():
    """
    MCP服务器信息和使用说明
    用于客户端了解如何连接和使用此MCP服务器
    """
    try:
        return jsonify({
            "name": current_app.mcp_server.name,
            "version": current_app.mcp_server.version,
            "protocol": {
                "name": "Model Context Protocol",
                "version": "1.0",
                "transport": "JSON-RPC 2.0 over HTTP"
            },
            "endpoint": {
                "url": "/mcp",
                "method": "POST",
                "contentType": "application/json"
            },
            "streaming": {
                "supported": True,
                "endpoint": "/mcp/stream/{stream_id}",
                "method": "GET",
                "contentType": "text/event-stream"
            },
            "capabilities": current_app.mcp_server.capabilities,
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for tool in current_app.mcp_server.tools
            ],
            "resources": [
                {
                    "uri": resource["uri"],
                    "name": resource["name"],
                    "description": resource["description"]
                }
                for resource in current_app.mcp_server.resources
            ],
            "usage": {
                "initialize": {
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "1.0",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "your-client-name",
                            "version": "1.0.0"
                        }
                    }
                },
                "example_requests": [
                    {
                        "description": "List available tools",
                        "request": {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/list",
                            "params": {}
                        }
                    },
                    {
                        "description": "Call audio separation tool",
                        "request": {
                            "jsonrpc": "2.0",
                            "id": 2,
                            "method": "tools/call",
                            "params": {
                                "name": "separate_audio",
                                "arguments": {
                                    "file_path": "/path/to/audio.mp3",
                                    "model": "htdemucs",
                                    "stems": ["vocals", "drums"],
                                    "stream_progress": True
                                }
                            }
                        }
                    }
                ]
            }
        })
    except Exception as e:
        logger.error(f"获取MCP信息失败: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500 