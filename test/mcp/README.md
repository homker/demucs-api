# 标准MCP (Model Context Protocol) 音频分离服务器

这是一个符合标准MCP协议的音频分离服务器，基于JSON-RPC 2.0实现，提供Demucs音频源分离功能。

## 🔧 **修正后的标准实现**

现在我们的MCP实现完全符合官方MCP协议规范：

### ✅ **协议特性**
- **JSON-RPC 2.0** - 标准JSON-RPC协议通信
- **单一端点** - 所有MCP通信通过 `/mcp` 端点
- **SSE流式输出** - 支持实时进度更新
- **完整工具集** - 音频分离、模型查询、状态查询
- **资源管理** - API文档和模型信息资源

### 🚀 **快速开始**

#### 1. 启动服务器
```bash
python run.py
```

#### 2. 服务器信息
访问 `http://localhost:8080/mcp/info` 获取服务器完整信息和使用示例。

#### 3. MCP端点配置
在MCP客户端中配置以下端点：
```
URL: http://localhost:8080/mcp
Method: POST
Content-Type: application/json
```

## 📋 **MCP协议使用**

### 初始化连接
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "1.0",
    "capabilities": {},
    "clientInfo": {
      "name": "your-client-name",
      "version": "1.0.0"
    }
  }
}
```

### 列出工具
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

### 调用音频分离
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "separate_audio",
    "arguments": {
      "file_path": "/path/to/audio.mp3",
      "model": "htdemucs",
      "stems": ["vocals", "drums"],
      "stream_progress": true
    }
  }
}
```

### 监听进度流
如果启用了 `stream_progress`，可以通过SSE端点获取实时进度：
```
GET http://localhost:8080/mcp/stream/{job_id}
```

## 🛠️ **可用工具**

1. **separate_audio** - 音频分离
   - `file_path`: 音频文件路径
   - `model`: 使用的模型 (htdemucs, htdemucs_ft, htdemucs_6s, mdx, mdx_q)
   - `stems`: 要分离的音轨类型数组
   - `stream_progress`: 是否启用流式进度输出

2. **get_models** - 获取可用模型列表

3. **get_job_status** - 获取任务状态
   - `job_id`: 任务ID

## 📚 **可用资源**

1. **demucs://docs/api** - API文档
2. **demucs://models/info** - 模型详细信息

## 🧪 **测试客户端**

### Python客户端
```bash
# 基础功能测试
python test/mcp/client.py --test basic

# 音频分离测试  
python test/mcp/client.py --test audio

# 完整测试
python test/mcp/client.py --test all
```

### 网页测试界面
访问 `http://localhost:8080/test/mcp` 使用可视化测试界面。

## 🔗 **与其他MCP客户端连接**

现在您可以在任何支持MCP的客户端中使用以下配置：

**MCP服务器端点:** `http://localhost:8080/mcp`
**协议:** JSON-RPC 2.0 over HTTP
**流式支持:** 是 (通过SSE)

这个标准实现可以与Claude Desktop、Cursor等支持MCP的工具无缝集成。

## 📊 **协议规范兼容性**

- ✅ JSON-RPC 2.0 消息格式
- ✅ 单一端点通信  
- ✅ 标准初始化握手
- ✅ 工具和资源管理
- ✅ 错误处理和状态码
- ✅ 流式进度支持 (扩展功能)

## 🎯 **与之前实现的区别**

**之前的实现：**
- 多个REST API端点
- 非标准协议格式
- 客户端需要知道多个URL

**标准MCP实现：**
- 单一JSON-RPC端点
- 完全符合MCP协议规范
- 标准客户端即可连接 