#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demucs全面测试脚本

这个脚本测试了Demucs应用程序的所有主要功能和接口，包括：
1. 模型加载和基本功能
2. API接口
3. 音频处理功能
4. 文件管理功能
"""

import os
import sys
import time
import json
import shutil
import unittest
import requests
import threading
from unittest import mock
from pathlib import Path

import torch
import numpy as np
from demucs import pretrained
from demucs.apply import apply_model
from demucs.audio import AudioFile, save_audio

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入应用相关模块
from app import create_app
from app.services.audio_separator import AudioSeparator
from app.services.file_manager import FileManager
from app.config import TestingConfig, get_config

class TestDemucsModel(unittest.TestCase):
    """测试Demucs模型基本功能"""
    
    def setUp(self):
        """初始化测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(self.test_dir, "test.mp3")
        self.device = "cpu"
        self.sample_rate = 44100
        self.channels = 2
    
    def test_model_loading(self):
        """测试模型加载"""
        print("\n===== 测试模型加载 =====")
        model = pretrained.get_model("htdemucs")
        self.assertIsNotNone(model, "模型加载失败")
        print(f"模型类型: {type(model)}")
        print(f"模型源轨道: {getattr(model, 'sources', None)}")
        
    def test_audio_loading(self):
        """测试音频加载"""
        print("\n===== 测试音频加载 =====")
        wav = AudioFile(self.test_file).read(
            streams=0, 
            samplerate=self.sample_rate, 
            channels=self.channels
        )
        self.assertIsNotNone(wav, "音频加载失败")
        self.assertEqual(len(wav.shape), 2, "音频形状不正确")
        print(f"音频形状: {wav.shape}")
    
    def test_audio_processing(self):
        """测试音频处理(含修复)"""
        print("\n===== 测试音频处理 =====")
        # 加载模型和音频
        model = pretrained.get_model("htdemucs")
        model.to(self.device)
        
        wav = AudioFile(self.test_file).read(
            streams=0, 
            samplerate=self.sample_rate, 
            channels=self.channels
        )
        
        # 添加batch维度
        input_wav = wav.to(self.device).unsqueeze(0)
        print(f"添加batch维度，新形状: {input_wav.shape}")
        
        # 应用模型
        try:
            sources = apply_model(
                model=model,
                mix=input_wav,
                shifts=1,
                split=True,
                overlap=0.25,
                progress=False,
                device=self.device
            )
            
            # 检查结果
            self.assertIsNotNone(sources, "音频处理失败")
            print(f"处理成功! 分离后音频形状: {sources.shape}")
            
            # 测试保存音频
            output_dir = os.path.join(self.test_dir, "output")
            os.makedirs(output_dir, exist_ok=True)
            
            if sources.dim() == 4 and sources.shape[0] == 1:
                sources = sources.squeeze(0)
                print(f"移除batch维度，最终形状: {sources.shape}")
            
            # 保存一个源为测试
            source_path = os.path.join(output_dir, "test_drums.wav")
            save_audio(sources[0], source_path, samplerate=self.sample_rate)
            self.assertTrue(os.path.exists(source_path), "音频保存失败")
            print(f"已保存音频文件: {source_path}")
            
        except Exception as e:
            self.fail(f"音频处理过程中出错: {str(e)}")


class TestAudioSeparatorService(unittest.TestCase):
    """测试AudioSeparator服务"""
    
    def setUp(self):
        """初始化测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(self.test_dir, "test.mp3")
        self.output_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 创建配置对象实例
        self.config = {
            'DEVICE': 'cpu',
            'SAMPLE_RATE': 44100,
            'CHANNELS': 2,
            'DEFAULT_MODEL': 'htdemucs'
        }
        
        # 创建服务实例
        self.separator = AudioSeparator(self.config)
    
    def test_service_initialization(self):
        """测试服务初始化"""
        print("\n===== 测试AudioSeparator服务初始化 =====")
        self.assertIsNotNone(self.separator, "服务初始化失败")
        self.assertEqual(self.separator.device, "cpu", "设备设置不正确")
        
        # 初始化模型
        self.separator.initialize()
        self.assertTrue(self.separator.models_loaded, "模型加载失败")
        print(f"已加载模型数量: {len(self.separator.models)}")
        print(f"可用模型列表: {self.separator.get_available_models()}")
    
    def test_audio_separation(self):
        """测试音频分离功能"""
        print("\n===== 测试音频分离功能 =====")
        # 确保模型已初始化
        if not hasattr(self.separator, 'models_loaded') or not self.separator.models_loaded:
            self.separator.initialize()
        
        # 进度更新回调
        progress_updates = []
        def progress_callback(job_id, progress, message, status=None, result=None):
            progress_updates.append({
                'job_id': job_id,
                'progress': progress,
                'message': message,
                'status': status,
                'result': result
            })
            print(f"进度更新: {progress}% - {message}")
        
        # 执行分离
        try:
            result = self.separator.separate_track(
                input_file=self.test_file,
                output_dir=self.output_dir,
                model_name="htdemucs",
                stems=["vocals", "drums"],
                progress_callback=progress_callback
            )
            
            # 验证结果
            self.assertIsNotNone(result, "分离过程返回空结果")
            self.assertIn('job_id', result, "结果中缺少job_id")
            self.assertIn('files', result, "结果中缺少files")
            self.assertTrue(len(result['files']) > 0, "未生成分离后的文件")
            
            # 打印结果信息
            print(f"分离完成，任务ID: {result['job_id']}")
            print(f"生成的文件数量: {len(result['files'])}")
            for file_info in result['files']:
                print(f"  - {file_info['stem']} ({file_info['name']})")
                self.assertTrue(os.path.exists(file_info['path']), f"文件不存在: {file_info['path']}")
            
        except Exception as e:
            self.fail(f"音频分离过程中出错: {str(e)}")


class TestFileManager(unittest.TestCase):
    """测试FileManager服务"""
    
    def setUp(self):
        """初始化测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(self.test_dir, "test.mp3")
        
        # 创建临时测试目录
        self.temp_upload_dir = os.path.join(self.test_dir, "temp_uploads")
        self.temp_output_dir = os.path.join(self.test_dir, "temp_outputs")
        os.makedirs(self.temp_upload_dir, exist_ok=True)
        os.makedirs(self.temp_output_dir, exist_ok=True)
        
        # 创建配置字典
        self.config = {
            'UPLOAD_FOLDER': self.temp_upload_dir,
            'OUTPUT_FOLDER': self.temp_output_dir,
            'ALLOWED_EXTENSIONS': {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'mp4'},
            'FILE_RETENTION_MINUTES': 60
        }
        
        # 创建服务实例
        self.file_manager = FileManager(self.config)
    
    def tearDown(self):
        """清理测试环境"""
        # 清理临时目录
        if os.path.exists(self.temp_upload_dir):
            shutil.rmtree(self.temp_upload_dir)
        if os.path.exists(self.temp_output_dir):
            shutil.rmtree(self.temp_output_dir)
    
    def test_job_directory_creation(self):
        """测试创建任务目录"""
        print("\n===== 测试创建任务目录 =====")
        job_id = "test-job-123"
        job_dir = self.file_manager.create_job_output_directory(job_id)
        
        self.assertTrue(os.path.exists(job_dir), "任务目录创建失败")
        print(f"已创建任务目录: {job_dir}")
    
    def test_file_upload_handling(self):
        """测试文件上传处理"""
        print("\n===== 测试文件上传处理 =====")
        
        # 模拟上传的文件
        from werkzeug.datastructures import FileStorage
        with open(self.test_file, 'rb') as f:
            mock_file = FileStorage(
                stream=f,
                filename="test_upload.mp3",
                content_type="audio/mp3"
            )
            
            # 保存上传文件
            filename, file_path = self.file_manager.save_uploaded_file(mock_file)
            
            # 验证
            self.assertTrue(os.path.exists(file_path), "上传文件保存失败")
            self.assertIn("test_upload", filename, "文件名处理有误")
            print(f"已保存上传文件: {file_path}")
    
    def test_zip_creation(self):
        """测试创建ZIP文件"""
        print("\n===== 测试创建ZIP文件 =====")
        
        # 创建一些测试文件
        test_files = []
        job_id = "test-zip-job-456"
        job_dir = self.file_manager.create_job_output_directory(job_id)
        
        for i in range(3):
            file_path = os.path.join(job_dir, f"test_file_{i}.txt")
            with open(file_path, 'w') as f:
                f.write(f"Test content {i}")
            test_files.append({
                'path': file_path,
                'name': f"test_file_{i}.txt",
                'stem': f"stem_{i}"
            })
        
        # 创建ZIP
        zip_path = self.file_manager.create_zip_from_files(test_files, job_id)
        
        # 验证
        self.assertTrue(os.path.exists(zip_path), "ZIP文件创建失败")
        self.assertTrue(zip_path.endswith('.zip'), "创建的不是ZIP文件")
        print(f"已创建ZIP文件: {zip_path}")
        
        # 清理测试文件
        for file_info in test_files:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])


class TestAPIEndpoints(unittest.TestCase):
    """测试API端点"""
    
    @classmethod
    def setUpClass(cls):
        """启动Flask应用进行测试"""
        # 创建一个测试专用应用
        os.environ['FLASK_ENV'] = 'testing'  # 使用测试配置
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        
        # 启动应用
        cls.port = 9876  # 使用不常用端口避免冲突
        cls.base_url = f"http://localhost:{cls.port}"
        
        # 设置自动关闭的标志
        cls.shutdown_event = threading.Event()
        
        # 在独立线程中运行应用
        def run_app():
            cls.app.run(host='localhost', port=cls.port, debug=False, use_reloader=False)
            
        cls.app_thread = threading.Thread(target=run_app)
        cls.app_thread.daemon = True
        cls.app_thread.start()
        
        # 等待应用启动
        time.sleep(1)
    
    @classmethod
    def tearDownClass(cls):
        """关闭Flask应用"""
        # 请求关闭
        try:
            requests.get(f"{cls.base_url}/shutdown")
        except:
            pass
        cls.shutdown_event.set()
    
    def setUp(self):
        """每个测试的设置"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(self.test_dir, "test.mp3")
    
    def test_models_endpoint(self):
        """测试获取模型列表端点"""
        print("\n===== 测试获取模型列表 =====")
        
        # 直接使用测试客户端请求
        response = self.client.get('/api/models')
        
        # 验证
        self.assertEqual(response.status_code, 200, "模型列表请求失败")
        data = json.loads(response.data)
        self.assertIn('status', data, "响应格式错误")
        self.assertEqual(data['status'], 'success', "请求状态不是成功")
        self.assertIn('data', data, "响应中没有数据")
        self.assertIn('models', data['data'], "响应中没有模型列表")
        
        print(f"可用模型: {data['data']['models']}")
    
    # 此测试需要处理复杂的文件上传逻辑，暂时注释
    # 在完整测试环境中再进行测试
    """
    def test_process_endpoint(self):
        测试音频处理端点
        print("\n===== 测试音频处理端点 =====")
        
        # 准备上传文件
        with open(self.test_file, 'rb') as f:
            file_content = f.read()
            
            # 创建测试文件内容
            data = {}
            data['file'] = (os.path.basename(self.test_file), file_content, 'audio/mp3')
            data['model'] = 'htdemucs'
            data['stems'] = 'vocals,drums'
            
            # 发送请求 - 使用Flask测试客户端的特殊方法
            response = self.client.post(
                '/api/process', 
                data=data,
                content_type='multipart/form-data'
            )
            
            # 验证
            self.assertEqual(response.status_code, 200, "处理请求失败")
            result = json.loads(response.data)
            self.assertEqual(result['status'], 'success', "请求状态不是成功")
            self.assertIn('job_id', result['data'], "响应中没有job_id")
            
            job_id = result['data']['job_id']
            print(f"任务已提交，ID: {job_id}")
            
            # 等待处理完成并检查状态
            max_retries = 60  # 最多等待60秒
            for i in range(max_retries):
                status_response = self.client.get(f'/api/status/{job_id}')
                status_data = json.loads(status_response.data)
                
                if status_response.status_code != 200:
                    print(f"状态请求失败: {status_data}")
                    break
                
                if 'data' in status_data and 'status' in status_data['data']:
                    status = status_data['data']['status']
                    progress = status_data['data'].get('progress', 0)
                    print(f"任务状态: {status}, 进度: {progress}%")
                    
                    if status == 'completed' or status == 'error':
                        break
                
                time.sleep(1)
            
            # 尝试获取结果文件信息
            if status == 'completed':
                print("任务已完成，检查下载链接")
                download_url = f"/api/download/{job_id}"
                
                # 验证文件是否可下载
                try:
                    # 直接请求下载端点可能会下载文件，这里我们只验证状态码
                    head_response = self.client.head(download_url)
                    self.assertIn(head_response.status_code, [200, 302], "下载链接无效")
                    print(f"下载链接有效，状态码: {head_response.status_code}")
                except Exception as e:
                    print(f"下载链接检查失败: {str(e)}")
    """


def run_tests():
    """运行所有测试"""
    # 设置测试套件
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_suite.addTests(loader.loadTestsFromTestCase(TestDemucsModel))
    test_suite.addTests(loader.loadTestsFromTestCase(TestAudioSeparatorService))
    test_suite.addTests(loader.loadTestsFromTestCase(TestFileManager))
    
    # API测试可能需要完整的应用环境，如果有问题可以注释掉
    test_suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 