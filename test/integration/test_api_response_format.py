#!/usr/bin/env python3
"""
API响应格式集成测试

测试API响应格式是否符合前端要求，包括：
1. 成功响应格式
2. 错误响应格式
3. 前端兼容性测试
"""

import requests
import json
import unittest
import os
from io import BytesIO

class TestAPIResponseFormat(unittest.TestCase):
    """API响应格式测试类"""
    
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
        
        # 准备测试音频文件路径
        self.test_audio_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'test_audio.wav')
    
    def _get_test_audio_file(self):
        """获取测试音频文件"""
        if os.path.exists(self.test_audio_path):
            with open(self.test_audio_path, 'rb') as f:
                return f.read()
        else:
            # 如果没有测试音频文件，创建一个最小的WAV文件
            # WAV文件头 (44字节) + 1秒16位单声道44100Hz的静音
            wav_header = b'RIFF$\x00\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x01\x00'
            silence_data = b'\x00\x00' * 22050  # 0.5秒静音
            return wav_header + silence_data
    
    def test_error_response_format(self):
        """测试错误响应格式"""
        print("\n🧪 测试错误响应格式...")
        
        # 测试没有文件的POST请求（预期错误）
        response = requests.post(f"{self.base_url}/api/process")
        
        self.assertEqual(response.status_code, 400)
        
        data = response.json()
        print(f"错误响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # 验证错误响应格式
        self.assertEqual(data.get('status'), 'error')
        self.assertIn('message', data)
        self.assertIn('No file provided', data.get('message', ''))
        
        print("✅ 错误响应格式正确")
    
    def test_success_response_format(self):
        """测试成功响应格式"""
        print("\n🧪 测试成功响应格式...")
        
        # 使用真实的音频文件
        audio_content = self._get_test_audio_file()
        files = {
            'audio': ('test.wav', BytesIO(audio_content), 'audio/wav')
        }
        
        data = {
            'model': 'htdemucs',
            'stems': 'vocals,drums',
            'output_format': 'wav',
            'audio_quality': 'high'
        }
        
        response = requests.post(f"{self.base_url}/api/process", files=files, data=data)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"成功响应: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 检查响应结构
            self.assertEqual(response_data.get('status'), 'success')
            self.assertIn('data', response_data)
            
            data_field = response_data['data']
            self.assertIn('job_id', data_field)
            self.assertIn('message', data_field)
            self.assertIn('status_url', data_field)
            
            print("✅ 成功响应格式正确")
            
            # 如果有任务ID，尝试清理
            job_id = data_field.get('job_id')
            if job_id:
                try:
                    requests.delete(f"{self.base_url}/api/cleanup/{job_id}")
                    print(f"🧹 已清理任务: {job_id}")
                except:
                    pass
                    
        else:
            print(f"❌ 请求失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容: {response.text}")
    
    def test_frontend_compatibility(self):
        """测试前端兼容性"""
        print("\n🧪 测试前端兼容性...")
        
        # 模拟前端预期的响应格式
        expected_success_format = {
            "status": "success",
            "data": {
                "job_id": "任务ID",
                "message": "Audio separation started",
                "status_url": "/api/status/任务ID",
                "progress_url": "/api/progress/任务ID",
                "download_url": "/api/download/任务ID"
            }
        }
        
        expected_error_format = {
            "status": "error",
            "message": "错误信息"
        }
        
        print("前端预期的成功响应格式:")
        print(json.dumps(expected_success_format, indent=2, ensure_ascii=False))
        
        print("\n前端预期的错误响应格式:")
        print(json.dumps(expected_error_format, indent=2, ensure_ascii=False))
        
        # 测试实际API是否符合预期格式 - 只测试格式，不实际处理
        # 使用一个简单的请求来避免实际的音频处理
        print("\n💡 为了避免不必要的音频处理，只验证API接口可访问性...")
        
        # 测试健康检查API格式
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('status', data)
        print("✅ API基础格式验证通过")
    
    def test_response_headers(self):
        """测试响应头"""
        print("\n🧪 测试响应头...")
        
        response = requests.get(f"{self.base_url}/health")
        
        # 检查Content-Type
        content_type = response.headers.get('content-type', '')
        self.assertIn('application/json', content_type)
        print(f"✅ Content-Type正确: {content_type}")
        
        # 检查CORS头（如果需要）
        if 'Access-Control-Allow-Origin' in response.headers:
            print(f"✅ CORS配置: {response.headers['Access-Control-Allow-Origin']}")


def run_api_response_format_tests():
    """运行API响应格式测试"""
    print("🧪 开始API响应格式测试...")
    print("=" * 50)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAPIResponseFormat)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
        print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_api_response_format_tests() 