#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子路径部署测试脚本

测试当应用部署在 https://domain.com/demucs/ 这样的子路径下时，
所有功能是否正常工作。
"""

import os
import sys
import json
import re
from pathlib import Path

# 在导入应用模块之前设置环境变量
os.environ['BASE_URL'] = '/demucs'
os.environ['APPLICATION_ROOT'] = '/demucs'

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.factory import create_app
from app.config import get_config

def test_subpath_deployment():
    """测试子路径部署配置"""
    
    print("🧪 测试子路径部署配置...")
    
    # 创建应用
    app = create_app(get_config())
    
    with app.test_client() as client:
        print("\n1. 测试主页渲染...")
        response = client.get('/')
        assert response.status_code == 200
        content = response.get_data(as_text=True)
        
        # 检查BASE_URL是否正确传递给JavaScript
        js_pattern = r'const BASE_URL = \"([^\"]*)\"\s*\|\|\s*window\.location\.origin;'
        match = re.search(js_pattern, content)
        assert match, "未找到JavaScript中的BASE_URL设置"
        assert match.group(1) == '/demucs', f"BASE_URL错误，期望'/demucs'，实际'{match.group(1)}'"
        print("✅ JavaScript BASE_URL设置正确: /demucs")
        
        # 检查静态文件路径
        assert '/demucs/static/js/mcp_sse_client.js' in content, "静态文件路径错误"
        print("✅ 静态文件路径正确: /demucs/static/js/mcp_sse_client.js")
        
        print("\n2. 测试API端点...")
        # 测试模型列表API
        response = client.get('/api/models')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'models' in data['data']
        print("✅ API端点正常工作")
        
        print("\n3. 测试MCP端点...")
        # 测试MCP初始化
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = client.post('/mcp', 
                             data=json.dumps(mcp_request),
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['jsonrpc'] == '2.0'
        assert 'result' in data
        print("✅ MCP端点正常工作")
        
        print("\n4. 测试健康检查...")
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        print("✅ 健康检查端点正常工作")
        
        print("\n5. 测试MCP测试页面...")
        response = client.get('/test/mcp')
        assert response.status_code == 200
        content = response.get_data(as_text=True)
        
        # 检查MCP测试页面的BASE_URL设置
        api_base_pattern = r'const API_BASE = ["\']([^"\']*)["\']'
        match = re.search(api_base_pattern, content)
        assert match, "未找到MCP测试页面中的API_BASE设置"
        assert match.group(1) == '/demucs', f"API_BASE错误，期望'/demucs'，实际'{match.group(1)}'"
        print("✅ MCP测试页面BASE_URL设置正确")

def test_api_urls_in_frontend():
    """测试前端JavaScript中的API URL构建是否正确"""
    
    print("\n🧪 测试前端API URL构建...")
    
    app = create_app(get_config())
    
    with app.test_client() as client:
        response = client.get('/')
        content = response.get_data(as_text=True)
        
        # 检查文档示例中的API URL
        expected_urls = [
            '${BASE_URL}/api/process',
            '${BASE_URL}/api/status/',
            '${BASE_URL}/api/progress/',
            '${BASE_URL}/api/download/'
        ]
        
        for url in expected_urls:
            assert url in content, f"未找到预期的API URL模式: {url}"
            print(f"✅ 找到API URL模式: {url}")

def test_subpath_urls():
    """测试子路径URL的工作方式"""
    
    print("\n🧪 测试子路径URL构建...")
    
    # 当BASE_URL为/demucs时，前端应该生成的URL：
    expected_frontend_urls = {
        'API请求': '/demucs/api/process',
        'SSE连接': '/demucs/api/progress/{job_id}',
        'MCP端点': '/demucs/mcp',
        'MCP流': '/demucs/mcp/stream/{job_id}',
        '下载': '/demucs/api/download/{job_id}',
        '静态文件': '/demucs/static/js/mcp_sse_client.js'
    }
    
    print("期望的前端URL构建结果:")
    for name, url in expected_frontend_urls.items():
        print(f"  {name}: {url}")
    
    # 对于部署在 https://whisper.ai.levelinfinite.com/demucs/ 的情况
    # 完整URL将是：
    base_domain = "https://whisper.ai.levelinfinite.com"
    print(f"\n在 {base_domain}/demucs/ 部署时的完整URL:")
    for name, url in expected_frontend_urls.items():
        full_url = f"{base_domain}{url}"
        print(f"  {name}: {full_url}")

def main():
    """运行所有测试"""
    
    print("=" * 60)
    print("子路径部署兼容性测试")
    print("=" * 60)
    
    try:
        test_subpath_deployment()
        test_api_urls_in_frontend()
        test_subpath_urls()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("✅ 应用已准备好在子路径部署")
        print("\n部署配置:")
        print("  BASE_URL=/demucs")
        print("  APPLICATION_ROOT=/demucs")
        print("\n部署URL示例:")
        print("  https://whisper.ai.levelinfinite.com/demucs/")
        print("=" * 60)
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n💥 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 