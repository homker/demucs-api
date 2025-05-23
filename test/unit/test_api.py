#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口测试脚本

该脚本测试所有应用API接口，包括:
1. 获取可用模型列表
2. 文件上传和音频处理
3. 状态查询
4. 进度监控（SSE连接）
5. 文件下载
6. 资源清理
7. 基础端点测试
"""

import os
import sys
import time
import json
import requests
import unittest
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置测试配置
TEST_HOST = "http://localhost:5001"
TEST_AUDIO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test.mp3")
TEST_TIMEOUT = 60  # 测试超时时间（秒）

class APITest(unittest.TestCase):
    """API接口测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 检查测试音频文件是否存在
        self.assertTrue(os.path.exists(TEST_AUDIO_FILE), f"测试音频文件不存在: {TEST_AUDIO_FILE}")
        
        # 检查服务器是否在线
        try:
            response = requests.get(f"{TEST_HOST}/health", timeout=5)
            self.assertEqual(response.status_code, 200, "服务器健康检查失败")
            data = response.json()
            self.assertEqual(data.get('status'), 'success', "服务器响应状态不正确")
            self.assertEqual(data.get('data', {}).get('status'), 'ok', "服务器状态不正常")
        except Exception as e:
            self.fail(f"服务器连接失败，请确保应用正在运行: {str(e)}")
        
        # 存储测试过程中创建的任务ID
        self.job_ids = []
    
    def tearDown(self):
        """测试后清理"""
        # 清理创建的所有任务
        for job_id in self.job_ids:
            try:
                requests.delete(f"{TEST_HOST}/api/cleanup/{job_id}")
            except:
                pass

    def test_00_basic_api_endpoints(self):
        """测试基础API端点"""
        print("\n===== 测试基础API端点 =====")
        
        # 测试健康检查
        response = requests.get(f"{TEST_HOST}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 健康检查正常")
        
        # 测试获取模型列表
        response = requests.get(f"{TEST_HOST}/api/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 模型列表API正常")
        
        # 测试获取支持格式
        response = requests.get(f"{TEST_HOST}/api/formats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 格式列表API正常")
        
        # 测试获取音质选项
        response = requests.get(f"{TEST_HOST}/api/qualities")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'success')
        print("✅ 音质选项API正常")

    def test_00_api_field_names(self):
        """测试不同字段名的API支持"""
        print("\n===== 测试API字段名兼容性 =====")
        
        # 创建模拟音频文件
        mock_audio_content = b"mock audio file content for testing"
        
        # 测试使用'audio'字段名
        print("测试'audio'字段名...")
        files = {'audio': ('test.mp3', BytesIO(mock_audio_content), 'audio/mp3')}
        data = {
            'model': 'htdemucs',
            'output_format': 'wav',
            'audio_quality': 'high'
        }
        
        response = requests.post(f"{TEST_HOST}/api/process", files=files, data=data)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'success':
                job_id = response_data.get('data', {}).get('job_id')
                if job_id:
                    self.job_ids.append(job_id)
                print("✅ 'audio'字段名测试成功")
            else:
                print(f"⚠️ 'audio'字段名响应异常: {response_data}")
        else:
            print(f"⚠️ 'audio'字段名请求失败: {response.status_code}")
        
        # 测试使用'file'字段名
        print("测试'file'字段名...")
        files = {'file': ('test.mp3', BytesIO(mock_audio_content), 'audio/mp3')}
        
        response = requests.post(f"{TEST_HOST}/api/process", files=files, data=data)
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'success':
                job_id = response_data.get('data', {}).get('job_id')
                if job_id:
                    self.job_ids.append(job_id)
                print("✅ 'file'字段名测试成功")
            else:
                print(f"⚠️ 'file'字段名响应异常: {response_data}")
        else:
            print(f"⚠️ 'file'字段名请求失败: {response.status_code}")

    def test_00_api_error_handling(self):
        """测试API错误处理"""
        print("\n===== 测试API错误处理 =====")
        
        # 测试没有文件的请求
        response = requests.post(f"{TEST_HOST}/api/process")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get('status'), 'error')
        self.assertIn('No file provided', data.get('message', ''))
        print("✅ 无文件请求错误处理正常")
        
        # 测试无效的任务ID查询
        response = requests.get(f"{TEST_HOST}/api/status/invalid-job-id")
        self.assertEqual(response.status_code, 404)
        print("✅ 无效任务ID错误处理正常")
    
    def test_01_list_models(self):
        """测试获取可用模型列表"""
        print("\n===== 测试获取可用模型 =====")
        
        # 发送请求
        response = requests.get(f"{TEST_HOST}/api/models")
        self.assertEqual(response.status_code, 200, "获取模型列表请求失败")
        
        # 解析响应
        data = response.json()
        self.assertEqual(data.get('status'), 'success', "获取模型列表失败")
        
        # 验证模型列表
        models_data = data.get('data', {})
        self.assertIn('models', models_data, "响应中缺少models字段")
        
        # 验证模型列表
        models = models_data.get('models', [])
        self.assertTrue(len(models) > 0, "模型列表为空")
        
        # 打印可用模型
        print(f"可用模型: {', '.join(models)}")
    
    def test_02_process_audio(self):
        """测试音频处理接口"""
        print("\n===== 测试音频处理 =====")
        
        # 准备请求数据
        with open(TEST_AUDIO_FILE, 'rb') as audio_file:
            files = {'file': audio_file}
            data = {
                'model': 'htdemucs',  # 使用默认模型
                'stems': 'vocals,drums'  # 只分离人声和鼓声以加快测试
            }
            
            # 发送请求
            response = requests.post(f"{TEST_HOST}/api/process", files=files, data=data)
            self.assertEqual(response.status_code, 200, "音频处理请求失败")
            
            # 解析响应
            data = response.json()
            self.assertEqual(data.get('status'), 'success', "音频处理启动失败")
            
            # 访问data字段
            response_data = data.get('data', {})
            self.assertIn('job_id', response_data, "响应中缺少job_id字段")
            
            # 记录任务ID用于后续测试
            job_id = response_data.get('job_id')
            self.job_ids.append(job_id)
            
            # 验证响应中的URL
            self.assertIn('status_url', response_data, "响应中缺少status_url字段")
            self.assertIn('progress_url', response_data, "响应中缺少progress_url字段")
            self.assertIn('download_url', response_data, "响应中缺少download_url字段")
            
            print(f"音频处理任务已创建: {job_id}")
            return job_id
    
    def test_03_get_status(self):
        """测试状态查询接口"""
        print("\n===== 测试状态查询 =====")
        
        # 首先创建一个处理任务
        job_id = self.test_02_process_audio()
        
        # 等待一秒让处理任务启动
        time.sleep(1)
        
        # 查询状态
        response = requests.get(f"{TEST_HOST}/api/status/{job_id}")
        self.assertEqual(response.status_code, 200, "状态查询请求失败")
        
        # 解析响应
        data = response.json()
        self.assertEqual(data.get('status'), 'success', "状态查询失败")
        
        # 访问data字段
        progress_data = data.get('data', {})
        self.assertIn('progress', progress_data, "响应中缺少progress字段")
        
        # 打印状态信息
        progress = progress_data.get('progress', 0)
        message = progress_data.get('message', '')
        print(f"任务状态: 进度={progress}%, 消息=\"{message}\"")
        
        # 测试不存在的任务ID
        response = requests.get(f"{TEST_HOST}/api/status/non-existent-id")
        self.assertEqual(response.status_code, 404, "对不存在的任务，应返回404状态码")
    
    def test_04_progress_sse(self):
        """测试SSE进度更新"""
        print("\n===== 测试SSE进度更新 =====")
        
        # 首先创建一个处理任务
        job_id = self.test_02_process_audio()
        
        # 创建进度更新接收器
        progress_updates = []
        stop_event = threading.Event()
        
        def progress_receiver():
            """接收SSE进度更新"""
            try:
                # 使用requests-sse库或手动处理SSE
                response = requests.get(
                    f"{TEST_HOST}/api/progress/{job_id}", 
                    stream=True,
                    headers={'Accept': 'text/event-stream'}
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    print(f"SSE连接失败: {response.status_code}")
                    return
                
                # 读取SSE事件
                for line in response.iter_lines():
                    if stop_event.is_set():
                        break
                        
                    if line:
                        line = line.decode('utf-8')
                        # 处理SSE格式
                        if line.startswith('data:'):
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                                progress_updates.append(data)
                                print(f"收到进度更新: {data}")
                                
                                # 如果进度完成或出错，退出
                                if data.get('status') in ['completed', 'error']:
                                    break
                            except json.JSONDecodeError:
                                print(f"无法解析进度数据: {data_str}")
            except Exception as e:
                print(f"SSE连接异常: {str(e)}")
        
        # 启动接收线程
        thread = threading.Thread(target=progress_receiver)
        thread.daemon = True
        thread.start()
        
        # 等待足够时间接收进度更新，或直到处理完成
        max_wait_time = TEST_TIMEOUT
        wait_interval = 0.5
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(wait_interval)
            elapsed_time += wait_interval
            
            # 检查是否有完成或错误状态的更新
            completed = False
            for update in progress_updates:
                if update.get('status') in ['completed', 'error']:
                    completed = True
                    break
            
            if completed or len(progress_updates) >= 5:  # 收到足够的更新或完成
                break
        
        # 停止接收线程
        stop_event.set()
        thread.join(timeout=2)
        
        # 验证收到的进度更新
        self.assertTrue(len(progress_updates) > 0, "没有收到任何进度更新")
        
        # 检查进度更新字段
        for update in progress_updates:
            self.assertIn('progress', update, "进度更新缺少progress字段")
            self.assertIn('message', update, "进度更新缺少message字段")
        
        # 检查进度是否递增
        if len(progress_updates) > 1:
            progress_values = [
                update.get('progress', 0) if isinstance(update.get('progress'), (int, float)) 
                else float(update.get('progress', 0)) 
                for update in progress_updates
            ]
            
            is_monotonic = True
            for i in range(1, len(progress_values)):
                if progress_values[i] < progress_values[i-1]:
                    is_monotonic = False
                    print(f"进度不单调: {progress_values[i-1]} -> {progress_values[i]}")
            
            self.assertTrue(is_monotonic, "进度值不是单调递增的")
    
    def test_05_download_result(self):
        """测试结果下载"""
        print("\n===== 测试结果下载 =====")
        
        # 首先创建一个处理任务
        job_id = self.test_02_process_audio()
        
        # 等待处理完成
        start_time = time.time()
        max_wait_time = TEST_TIMEOUT
        completed = False
        
        print(f"等待任务完成，最多等待{max_wait_time}秒...")
        while time.time() - start_time < max_wait_time:
            response = requests.get(f"{TEST_HOST}/api/status/{job_id}")
            if response.status_code == 200:
                data = response.json()
                
                # 适应API响应结构
                if data.get('status') == 'success':
                    progress_data = data.get('data', {})
                    
                    if progress_data.get('status') == 'completed':
                        completed = True
                        print(f"任务已完成，用时: {time.time() - start_time:.1f}秒")
                        break
                    elif progress_data.get('status') == 'error':
                        self.fail(f"任务处理出错: {progress_data.get('message')}")
                        break
                    
                    # 打印当前进度
                    progress = progress_data.get('progress', 0)
                    print(f"当前进度: {progress}%")
            
            time.sleep(2)  # 等待2秒后再次查询
        
        # 如果任务没有完成，测试失败
        self.assertTrue(completed, f"任务在{max_wait_time}秒内未完成")
        
        # 下载结果
        response = requests.get(f"{TEST_HOST}/api/download/{job_id}", stream=True)
        self.assertEqual(response.status_code, 200, "下载请求失败")
        
        # 检查响应头
        self.assertIn('Content-Type', response.headers, "响应缺少Content-Type头")
        self.assertEqual(response.headers['Content-Type'], 'application/zip', "响应类型不是zip文件")
        self.assertIn('Content-Disposition', response.headers, "响应缺少Content-Disposition头")
        
        # 下载文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=128):
                temp_file.write(chunk)
            temp_path = temp_file.name
        
        # 验证文件存在且大小合理
        self.assertTrue(os.path.exists(temp_path), "下载的文件不存在")
        file_size = os.path.getsize(temp_path)
        self.assertTrue(file_size > 1000, f"文件太小: {file_size}字节")
        
        print(f"成功下载文件，大小: {file_size/1024:.2f} KB")
        
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass
    
    def test_06_cleanup(self):
        """测试资源清理接口"""
        print("\n===== 测试资源清理 =====")
        
        # 首先创建一个处理任务
        job_id = self.test_02_process_audio()
        
        # 等待一会儿让任务开始
        time.sleep(2)
        
        # 请求清理
        response = requests.delete(f"{TEST_HOST}/api/cleanup/{job_id}")
        self.assertEqual(response.status_code, 200, "清理请求失败")
        
        # 解析响应
        data = response.json()
        self.assertEqual(data.get('status'), 'success', "清理操作失败")
        
        # 验证任务已被清理
        response = requests.get(f"{TEST_HOST}/api/status/{job_id}")
        self.assertEqual(response.status_code, 404, "任务清理后应返回404状态码")
        
        print(f"成功清理任务: {job_id}")
        
        # 从待清理列表中移除
        if job_id in self.job_ids:
            self.job_ids.remove(job_id)
    
    def test_07_negative_cases(self):
        """测试错误情况处理"""
        print("\n===== 测试错误情况处理 =====")
        
        # 测试上传无效文件类型
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
            temp_file.write(b'This is not an audio file')
            temp_file.flush()
            
            with open(temp_file.name, 'rb') as invalid_file:
                files = {'file': invalid_file}
                response = requests.post(f"{TEST_HOST}/api/process", files=files)
                self.assertNotEqual(response.status_code, 200, "无效文件类型应被拒绝")
                print("成功拒绝无效文件类型")
        
        # 测试下载不存在的任务
        response = requests.get(f"{TEST_HOST}/api/download/non-existent-id")
        self.assertEqual(response.status_code, 404, "下载不存在的任务应返回404状态码")
        print("成功处理不存在的下载请求")


if __name__ == '__main__':
    unittest.main() 