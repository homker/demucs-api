#!/usr/bin/env python3
"""
下载功能测试模块
Tests download functionality for audio separation results
"""

import unittest
import requests
import time
import os
import json
import zipfile
import tempfile

class TestDownloadFunctionality(unittest.TestCase):
    """下载功能测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.api_base = "http://127.0.0.1:8080/api"
        cls.test_audio = "test.mp3"  # 从test目录运行时的相对路径
        cls.timeout = 300  # 5分钟超时
        
        # 确保测试音频文件存在
        if not os.path.exists(cls.test_audio):
            raise unittest.SkipTest(f"测试音频文件不存在: {cls.test_audio}")
    
    def test_download_nonexistent_job(self):
        """测试下载不存在的任务"""
        print("\n🧪 测试下载不存在的任务...")
        
        fake_job_id = "non-existent-job-id"
        response = requests.get(f"{self.api_base}/download/{fake_job_id}")
        
        self.assertEqual(response.status_code, 404, 
                        f"期望404状态码，实际得到: {response.status_code}")
        
        result = response.json()
        self.assertEqual(result['status'], 'error', 
                        "期望返回错误状态")
        print("✅ 不存在的Job ID正确返回404")
    
    def test_download_incomplete_job(self):
        """测试下载未完成的任务"""
        print("\n🧪 测试下载未完成的任务...")
        
        # 提交一个任务但不等待完成
        with open(self.test_audio, 'rb') as f:
            files = {'file': f}
            data = {'model': 'htdemucs', 'stems': 'vocals'}
            response = requests.post(f"{self.api_base}/process", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'success')
        
        job_id = result['data']['job_id']
        
        # 立即尝试下载（任务还未完成）
        download_response = requests.get(f"{self.api_base}/download/{job_id}")
        
        # 应该返回400状态码（任务未完成）
        self.assertEqual(download_response.status_code, 400,
                        "下载未完成的任务应该返回400状态码")
        
        print(f"✅ 未完成任务正确返回400状态码")
        
        # 清理任务
        requests.delete(f"{self.api_base}/cleanup/{job_id}")
    
    def test_complete_download_workflow(self):
        """测试完整的下载工作流程"""
        print("\n🧪 测试完整的下载工作流程...")
        
        # 1. 提交处理请求
        print("📤 提交音频分离请求...")
        with open(self.test_audio, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals'  # 只处理人声，加快测试速度
            }
            response = requests.post(f"{self.api_base}/process", files=files, data=data)
        
        self.assertEqual(response.status_code, 200, 
                        f"提交请求失败: {response.status_code}")
        
        result = response.json()
        self.assertEqual(result['status'], 'success', 
                        f"请求返回失败: {result}")
        
        job_id = result['data']['job_id']
        download_url = result['data']['download_url']
        
        print(f"✅ 任务已提交，Job ID: {job_id}")
        
        # 2. 等待任务完成
        print("⏳ 等待任务完成...")
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < self.timeout:
            status_response = requests.get(f"{self.api_base}/status/{job_id}")
            
            self.assertEqual(status_response.status_code, 200, 
                           "状态查询失败")
            
            status_data = status_response.json()
            self.assertEqual(status_data['status'], 'success', 
                           "状态数据格式错误")
            
            progress_info = status_data['data']
            progress = progress_info['progress']
            status = progress_info['status']
            message = progress_info.get('message', '')
            
            print(f"📊 进度: {progress}% - {status} - {message}")
            
            if status == 'completed':
                print("✅ 任务完成!")
                completed = True
                break
            elif status == 'error':
                self.fail(f"任务处理失败: {message}")
            
            time.sleep(2)
        
        self.assertTrue(completed, "任务在超时时间内未完成")
        
        # 3. 测试下载功能
        print("📥 测试下载功能...")
        download_response = requests.get(f"{self.api_base}/download/{job_id}")
        
        self.assertEqual(download_response.status_code, 200, 
                        f"下载失败: {download_response.status_code}")
        
        # 验证响应头
        content_type = download_response.headers.get('content-type', '')
        content_disposition = download_response.headers.get('content-disposition', '')
        
        self.assertIn('application/zip', content_type.lower(), 
                     "内容类型应该是ZIP文件")
        self.assertIn('attachment', content_disposition.lower(), 
                     "应该是附件下载")
        
        print(f"✅ 下载成功!")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disposition}")
        print(f"   文件大小: {len(download_response.content)} bytes")
        
        # 4. 验证ZIP文件内容
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(download_response.content)
            temp_file_path = temp_file.name
        
        try:
            self.assertTrue(os.path.exists(temp_file_path), 
                           "临时ZIP文件应该存在")
            self.assertGreater(os.path.getsize(temp_file_path), 0, 
                              "ZIP文件不应该为空")
            
            # 验证ZIP文件结构
            with zipfile.ZipFile(temp_file_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                self.assertGreater(len(file_list), 0, 
                                  "ZIP文件应该包含文件")
                
                # 检查文件名格式
                for filename in file_list:
                    self.assertTrue(filename.endswith('.wav'), 
                                   f"音频文件应该是WAV格式: {filename}")
                
                print(f"   ZIP文件内容: {file_list}")
            
            print("✅ ZIP文件验证通过")
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        # 5. 清理测试资源
        cleanup_response = requests.delete(f"{self.api_base}/cleanup/{job_id}")
        self.assertEqual(cleanup_response.status_code, 200, 
                        "资源清理失败")
        print("✅ 测试资源已清理")
    
    def test_download_zip_content_integrity(self):
        """测试ZIP文件内容完整性"""
        print("\n🧪 测试ZIP文件内容完整性...")
        
        # 提交处理所有音轨的任务
        with open(self.test_audio, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals,drums,bass,other'  # 处理所有音轨
            }
            response = requests.post(f"{self.api_base}/process", files=files, data=data)
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        job_id = result['data']['job_id']
        
        # 等待完成
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            status_response = requests.get(f"{self.api_base}/status/{job_id}")
            status_data = status_response.json()
            
            if status_data['data']['status'] == 'completed':
                break
            elif status_data['data']['status'] == 'error':
                self.fail("任务处理失败")
            
            time.sleep(2)
        
        # 下载并验证
        download_response = requests.get(f"{self.api_base}/download/{job_id}")
        self.assertEqual(download_response.status_code, 200)
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(download_response.content)
            temp_file_path = temp_file.name
        
        try:
            with zipfile.ZipFile(temp_file_path, 'r') as zip_file:
                file_list = zip_file.namelist()
                
                # 验证每个请求的音轨都存在
                expected_stems = ['vocals', 'drums', 'bass', 'other']
                for stem in expected_stems:
                    stem_files = [f for f in file_list if stem in f.lower()]
                    self.assertGreater(len(stem_files), 0, 
                                      f"应该包含{stem}音轨文件")
                
                print(f"✅ ZIP包含所有期望的音轨: {file_list}")
        
        finally:
            os.remove(temp_file_path)
            requests.delete(f"{self.api_base}/cleanup/{job_id}")

def run_download_tests():
    """运行下载功能测试的函数入口"""
    print("🚀 下载功能测试")
    print("="*50)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDownloadFunctionality)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*50)
    print("📊 下载功能测试结果总结:")
    print(f"   运行测试数: {result.testsRun}")
    print(f"   失败数: {len(result.failures)}")
    print(f"   错误数: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有下载功能测试通过!")
        return True
    else:
        print("\n⚠️ 部分下载功能测试失败")
        return False

if __name__ == "__main__":
    # 直接运行时的测试
    run_download_tests() 