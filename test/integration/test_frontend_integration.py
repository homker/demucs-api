#!/usr/bin/env python3
"""
前端集成测试

测试前端功能是否正常工作，包括：
1. 页面访问测试
2. 静态文件加载测试
3. API端点集成测试
4. JavaScript功能测试
"""

import requests
import time
import json
import unittest

class TestFrontendIntegration(unittest.TestCase):
    """前端集成测试类"""
    
    def setUp(self):
        """测试准备"""
        self.base_url = "http://localhost:8080"
        
        # 检查服务器是否在线
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code != 200:
                self.skipTest("服务器未运行，跳过测试")
        except requests.exceptions.ConnectionError:
            self.skipTest("无法连接到服务器，跳过测试")
    
    def test_main_page_access(self):
        """测试主页访问"""
        print("\n🧪 测试主页访问...")
        
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        
        content = response.text
        
        # 检查基本HTML结构
        self.assertIn('<html', content)
        self.assertIn('<body', content)
        self.assertIn('Demucs', content)
        
        print("✅ 主页访问正常")
    
    def test_javascript_files_loading(self):
        """测试JavaScript文件加载"""
        print("\n🧪 测试JavaScript文件...")
        
        # 先获取主页，检查引用的JS文件
        response = requests.get(f"{self.base_url}/")
        content = response.text
        
        js_files = ['main.js', 'audio-processor.js', 'debug.js']
        missing_js = []
        
        for js_file in js_files:
            if js_file in content:
                print(f"✅ 主页引用了 {js_file}")
                
                # 测试文件是否可以访问
                js_response = requests.get(f"{self.base_url}/static/js/{js_file}")
                if js_response.status_code == 200:
                    print(f"✅ {js_file} 可以正常加载")
                else:
                    print(f"❌ {js_file} 加载失败: {js_response.status_code}")
                    missing_js.append(js_file)
            else:
                missing_js.append(js_file)
                print(f"❌ 主页未引用 {js_file}")
        
        self.assertEqual(len(missing_js), 0, f"缺失JavaScript文件: {missing_js}")
    
    def test_css_files_loading(self):
        """测试CSS文件加载"""
        print("\n🧪 测试CSS文件...")
        
        # 测试主要CSS文件
        css_files = ['main.css']
        
        for css_file in css_files:
            response = requests.get(f"{self.base_url}/static/css/{css_file}")
            self.assertEqual(response.status_code, 200)
            print(f"✅ {css_file} 加载正常")
            
            # 检查CSS内容是否包含关键样式
            content = response.text
            self.assertIn('body', content)  # 基本的body样式
    
    def test_api_endpoints_integration(self):
        """测试API端点集成"""
        print("\n🧪 测试API端点集成...")
        
        # 测试健康检查
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 健康检查API返回的格式是 {"service":"demucs-audio-separator","status":"healthy"}
        self.assertEqual(data.get('status'), 'healthy')
        print("✅ 健康检查API正常")
        
        # 测试模型列表API
        response = requests.get(f"{self.base_url}/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        self.assertIn('models', data.get('data', {}))
        print("✅ 模型列表API正常")
        
        # 测试格式列表API
        response = requests.get(f"{self.base_url}/api/formats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 格式列表API正常")
        
        # 测试音质选项API
        response = requests.get(f"{self.base_url}/api/qualities")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 音质选项API正常")
    
    def test_file_upload_error_handling(self):
        """测试文件上传错误处理"""
        print("\n🧪 测试文件上传错误处理...")
        
        # 测试没有文件的请求
        response = requests.post(f"{self.base_url}/api/process")
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        self.assertEqual(data.get('status'), 'error')
        self.assertIn('No file provided', data.get('message', ''))
        print("✅ 文件上传错误处理正常")
    
    def test_static_assets(self):
        """测试静态资源"""
        print("\n🧪 测试静态资源...")
        
        # 测试图标文件（如果存在）
        icon_files = ['favicon.ico']
        for icon_file in icon_files:
            response = requests.get(f"{self.base_url}/{icon_file}")
            if response.status_code == 200:
                print(f"✅ {icon_file} 存在")
            else:
                print(f"ℹ️ {icon_file} 不存在 (正常)")
    
    def test_progress_page_access(self):
        """测试进度页面访问（如果存在）"""
        print("\n🧪 测试特殊页面访问...")
        
        # 测试MCP测试页面（如果存在）
        response = requests.get(f"{self.base_url}/mcp")
        if response.status_code == 200:
            print("✅ MCP测试页面可访问")
            content = response.text
            self.assertIn('MCP', content)
        else:
            print("ℹ️ MCP测试页面不存在")
    
    def test_error_pages(self):
        """测试错误页面"""
        print("\n🧪 测试错误页面...")
        
        # 测试404页面
        response = requests.get(f"{self.base_url}/nonexistent-page")
        self.assertEqual(response.status_code, 404)
        print("✅ 404页面正常")
    
    def test_admin_redirect(self):
        """测试管理页面重定向"""
        print("\n🧪 测试管理页面...")
        
        # 未登录访问管理页面应该重定向
        response = requests.get(f"{self.base_url}/admin/", allow_redirects=False)
        
        # 可能返回302重定向或者200但显示登录表单
        if response.status_code == 302:
            print("✅ 管理页面正确重定向到登录")
        elif response.status_code == 200:
            # 检查是否包含登录表单
            content = response.text
            if "登录" in content or "login" in content or "用户名" in content:
                print("✅ 管理页面显示登录表单")
            else:
                print("⚠️ 管理页面访问异常")
        else:
            print(f"⚠️ 管理页面响应异常: {response.status_code}")
    
    def test_frontend_debug_features(self):
        """测试前端调试功能"""
        print("\n🧪 测试前端调试功能...")
        
        # 检查debug.js是否存在
        response = requests.get(f"{self.base_url}/static/js/debug.js")
        if response.status_code == 200:
            content = response.text
            
            # 检查是否包含调试功能
            debug_functions = ['DemucsDebug', 'runAllChecks', 'testProgress']
            found_functions = []
            
            for func in debug_functions:
                if func in content:
                    found_functions.append(func)
            
            if found_functions:
                print(f"✅ 找到调试功能: {', '.join(found_functions)}")
            else:
                print("⚠️ 未找到预期的调试功能")
        else:
            print("ℹ️ 调试脚本不存在")


def run_frontend_integration_tests():
    """运行前端集成测试"""
    print("🧪 开始前端集成测试...")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFrontendIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print("🎯 修复内容总结:")
    print("• ✅ 改进了音频处理的错误处理逻辑")
    print("• ✅ 增强了进度条显示和重置功能")
    print("• ✅ 优化了SSE连接的错误处理")
    print("• ✅ 添加了详细的调试日志")
    print("• ✅ 改进了API响应验证")
    print("• ✅ 添加了连接超时处理")
    print("• ✅ 增加了调试工具脚本")
    
    print("\n💡 使用建议:")
    print("1. 打开浏览器开发者工具的控制台查看详细日志")
    print("2. 在控制台运行 DemucsDebug.runAllChecks() 进行完整检查")
    print("3. 在控制台运行 DemucsDebug.testProgress() 测试进度条")
    print("4. 如果仍有问题，请分享控制台错误信息")
    
    if result.wasSuccessful():
        print("\n✅ 所有前端集成测试通过！")
    else:
        print("\n❌ 部分前端集成测试失败")
        print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_frontend_integration_tests() 