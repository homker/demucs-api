#!/usr/bin/env python3
"""
音频格式和质量控制功能测试模块 (完整版本)
Tests audio format and quality control functionality (full version)
包含所有格式的测试，包括耗时的FLAC无损压缩测试
"""

import unittest
import requests
import os
import tempfile
import shutil
from pathlib import Path

class TestAudioFormatQualityFull(unittest.TestCase):
    """音频格式和质量控制测试类 (完整版本，包含FLAC)"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.api_base = "http://127.0.0.1:8080"
        cls.test_file = Path(__file__).parent.parent / "test.mp3"
        cls.temp_dir = tempfile.mkdtemp()
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_get_supported_formats(self):
        """测试获取支持的音频格式"""
        print("\n🎵 测试获取支持的音频格式...")
        
        response = requests.get(f"{self.api_base}/api/formats")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('formats', data['data'])
        self.assertIn('default', data['data'])
        
        formats = data['data']['formats']
        self.assertIn('wav', formats)
        self.assertIn('mp3', formats)
        self.assertIn('flac', formats)
        
        print(f"✅ 支持的格式: {formats}")
        print(f"✅ 默认格式: {data['data']['default']}")
    
    def test_get_quality_options(self):
        """测试获取音频质量选项"""
        print("\n🎧 测试获取音频质量选项...")
        
        response = requests.get(f"{self.api_base}/api/qualities")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('qualities', data['data'])
        self.assertIn('default', data['data'])
        
        qualities = data['data']['qualities']
        self.assertIn('low', qualities)
        self.assertIn('medium', qualities)
        self.assertIn('high', qualities)
        self.assertIn('lossless', qualities)
        
        print(f"✅ 质量选项: {list(qualities.keys())}")
        print(f"✅ 默认质量: {data['data']['default']}")
        
        # 验证质量描述
        for quality, description in qualities.items():
            self.assertIsInstance(description, str)
            self.assertTrue(len(description) > 0)
            print(f"   {quality}: {description}")
    
    def test_audio_separation_with_mp3_high(self):
        """测试MP3高质量音频分离"""
        print("\n🎵 测试MP3高质量音频分离...")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'mp3',
                'audio_quality': 'high'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('job_id', result['data'])
            
            job_id = result['data']['job_id']
            print(f"✅ MP3高质量分离任务创建成功: {job_id}")
    
    def test_audio_separation_with_mp3_medium(self):
        """测试MP3中等质量音频分离"""
        print("\n🎵 测试MP3中等质量音频分离...")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'mp3',
                'audio_quality': 'medium'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('job_id', result['data'])
            
            job_id = result['data']['job_id']
            print(f"✅ MP3中等质量分离任务创建成功: {job_id}")
    
    def test_audio_separation_with_wav_high(self):
        """测试WAV高质量音频分离"""
        print("\n🎵 测试WAV高质量音频分离...")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'wav',
                'audio_quality': 'high'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('job_id', result['data'])
            
            job_id = result['data']['job_id']
            print(f"✅ WAV高质量分离任务创建成功: {job_id}")
    
    def test_audio_separation_with_flac_lossless(self):
        """测试FLAC无损音频分离（耗时测试）"""
        print("\n🎵 测试FLAC无损音频分离...")
        print("⚠️  注意：此测试可能需要较长时间，包含FLAC编码过程")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'flac',
                'audio_quality': 'lossless'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            self.assertEqual(result['status'], 'success')
            self.assertIn('job_id', result['data'])
            
            job_id = result['data']['job_id']
            print(f"✅ FLAC无损分离任务创建成功: {job_id}")
    
    def test_invalid_format_rejection(self):
        """测试无效格式被正确拒绝"""
        print("\n❌ 测试无效格式拒绝...")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'invalid_format',
                'audio_quality': 'high'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 400)
            result = response.json()
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('不支持的输出格式', result['message'])
            
            print(f"✅ 无效格式正确被拒绝")
    
    def test_invalid_quality_rejection(self):
        """测试无效质量被正确拒绝"""
        print("\n❌ 测试无效质量拒绝...")
        
        if not self.test_file.exists():
            self.skipTest("测试音频文件不存在")
        
        with open(self.test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'mp3',
                'audio_quality': 'invalid_quality'
            }
            
            response = requests.post(f"{self.api_base}/api/process", 
                                   files=files, data=data)
            
            self.assertEqual(response.status_code, 400)
            result = response.json()
            
            self.assertEqual(result['status'], 'error')
            self.assertIn('不支持的音频质量', result['message'])
            
            print(f"✅ 无效质量正确被拒绝")

def run_format_quality_full_tests():
    """运行完整音频格式和质量测试的函数入口"""
    print("🎵 音频格式和质量控制功能测试 (完整版本)")
    print("⚠️  注意：此测试包含耗时的FLAC无损压缩测试")
    print("="*60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAudioFormatQualityFull)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*60)
    print("📊 完整格式和质量测试结果总结:")
    print(f"   运行测试数: {result.testsRun}")
    print(f"   失败数: {len(result.failures)}")
    print(f"   错误数: {len(result.errors)}")
    print(f"   测试格式: WAV, MP3, FLAC (包含无损测试)")
    
    if result.wasSuccessful():
        print("\n🎉 所有完整格式和质量测试通过!")
        return True
    else:
        print("\n⚠️ 部分完整格式和质量测试失败")
        return False

if __name__ == "__main__":
    # 直接运行时的完整测试
    print("🚀 启动完整测试模式...")
    run_format_quality_full_tests() 