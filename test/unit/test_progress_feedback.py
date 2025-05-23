#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试音频分离进度反馈功能

这个测试文件验证音频分离过程中的进度反馈功能是否正确工作
"""

import os
import sys
import time
import unittest
import threading
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestProgressFeedback(unittest.TestCase):
    """测试音频分离进度反馈功能"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_file = os.path.join(self.test_dir, "test.mp3")
        self.output_dir = os.path.join(self.test_dir, "output")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 导入必要的模块
        from app.config import get_config
        self.config_obj = get_config()  # 这是一个配置类，不是字典
        
        # 创建配置字典以便在测试中使用
        self.config = {
            'SAMPLE_RATE': self.config_obj.SAMPLE_RATE,
            'CHANNELS': self.config_obj.CHANNELS,
            'DEFAULT_MODEL': self.config_obj.DEFAULT_MODEL
        }
        
        # 创建音频分离服务
        from app.services.audio_separator import AudioSeparator
        self.separator = AudioSeparator(self.config)
    
    def test_progress_callback_functionality(self):
        """测试进度回调功能"""
        print("\n===== 测试进度回调功能 =====")
        
        # 确保模型已初始化
        if not hasattr(self.separator, 'models_loaded') or not self.separator.models_loaded:
            self.separator.initialize()
        
        # 创建进度记录列表
        progress_updates = []
        progress_timestamps = []
        last_progress = -1
        progress_lock = threading.Lock()
        
        # 进度更新回调
        def progress_callback(progress, message, status=None, result=None):
            with progress_lock:
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                job_id = "test-job-id"  # 测试使用固定ID
                progress_updates.append({
                    'job_id': job_id,
                    'progress': progress,
                    'message': message,
                    'status': status,
                    'result': result,
                    'time': now
                })
                progress_timestamps.append(time.time())
                nonlocal last_progress
                
                # 确保进度值是数字
                progress_value = progress if isinstance(progress, (int, float)) else 0
                
                # 只打印进度变化或者重要消息
                if progress_value != last_progress or status == 'error' or status == 'completed':
                    print(f"[{now}] 进度: {progress_value}% - {message}")
                    last_progress = progress_value
        
        # 执行分离
        try:
            start_time = time.time()
            
            # 为了测试的可靠性，使用一个小的测试样本
            result = self.separator.separate_track(
                input_file=self.test_file,
                output_dir=self.output_dir,
                model_name="htdemucs",  # 使用单个模型以加快测试速度
                stems=["vocals"],  # 只分离人声以加快测试速度
                progress_callback=progress_callback
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 验证基本结果
            self.assertIsNotNone(result, "分离过程返回空结果")
            self.assertIn('job_id', result, "结果中缺少job_id")
            self.assertIn('files', result, "结果中缺少files")
            self.assertTrue(len(result['files']) > 0, "未生成分离后的文件")
            
            # 分析进度更新情况
            with progress_lock:
                update_count = len(progress_updates)
                
                # 输出进度更新统计信息
                print(f"\n总进度更新次数: {update_count}")
                print(f"总处理时间: {duration:.2f}秒")
                
                if update_count > 0:
                    # 验证关键进度点
                    has_start = False
                    has_loading = False
                    has_processing = False
                    has_completed = False
                    
                    for update in progress_updates:
                        prog = update['progress']
                        msg = update['message']
                        
                        # 确保进度值是数字
                        prog_value = prog if isinstance(prog, (int, float)) else 0
                        
                        # 检查关键进度点
                        if prog_value == 0 and "开始" in msg:
                            has_start = True
                        elif prog_value < 10 and "加载" in msg:
                            has_loading = True
                        elif prog_value >= 10 and prog_value < 95:
                            has_processing = True
                        elif prog_value == 100 and "完成" in msg:
                            has_completed = True
                    
                    # 验证是否包含所有关键进度点
                    self.assertTrue(has_start, "没有起始进度点(0%)")
                    self.assertTrue(has_loading, "没有加载进度点(<10%)")
                    self.assertTrue(has_processing, "没有处理进度点(10-95%)")
                    self.assertTrue(has_completed, "没有完成进度点(100%)")
                    
                    # 验证进度的增长是否合理
                    prev_progress = -1
                    monotonic = True
                    for update in progress_updates:
                        # 确保进度值是数字
                        current_progress = update['progress'] if isinstance(update['progress'], (int, float)) else 0
                        if current_progress < prev_progress:
                            monotonic = False
                            print(f"进度不单调: {prev_progress}% -> {current_progress}%")
                        prev_progress = current_progress
                    
                    self.assertTrue(monotonic, "进度值不是单调增长的")
                    
                    # 验证进度更新频率
                    if len(progress_timestamps) > 1:
                        intervals = [progress_timestamps[i] - progress_timestamps[i-1] 
                                     for i in range(1, len(progress_timestamps))]
                        avg_interval = sum(intervals) / len(intervals)
                        print(f"平均进度更新间隔: {avg_interval:.2f}秒")
                        
                        # 通常进度更新间隔应该在合理范围内
                        # 不要太频繁(避免性能问题)，也不要太稀疏(用户体验不好)
                        # 这里使用一个宽松的判断条件
                        self.assertTrue(0.1 <= avg_interval <= 10.0, 
                                      f"进度更新间隔({avg_interval:.2f}秒)不在合理范围内")
                else:
                    self.fail("没有接收到任何进度更新")
            
            # 打印生成的文件信息
            print(f"分离完成，任务ID: {result['job_id']}")
            print(f"生成的文件数量: {len(result['files'])}")
            for file_info in result['files']:
                print(f"  - {file_info['stem']} ({file_info['name']})")
                # 检查文件是否存在且大小合理
                file_path = file_info['path']
                self.assertTrue(os.path.exists(file_path), f"文件不存在: {file_path}")
                
                # 检查文件大小是否合理 (不应该太小)
                file_size = os.path.getsize(file_path)
                print(f"    文件大小: {file_size/1024:.2f} KB")
                self.assertTrue(file_size > 1000, f"文件太小: {file_size}字节")
            
        except Exception as e:
            self.fail(f"音频分离过程中出错: {str(e)}")
    
    def test_apply_model_with_progress(self):
        """测试apply_model_with_progress包装函数"""
        print("\n===== 测试apply_model_with_progress包装函数 =====")
        
        # 确保模型已初始化
        if not hasattr(self.separator, 'models_loaded') or not self.separator.models_loaded:
            self.separator.initialize()
        
        # 获取模型
        model_name = "htdemucs"
        models = self.separator._get_model(model_name)
        self.assertTrue(len(models) > 0, "获取模型失败")
        model = models[0]
        
        # 进度更新记录
        progress_updates = []
        
        # 进度回调
        def test_callback(progress, message, status=None, result=None):
            # 确保进度值是数字
            progress_value = progress if isinstance(progress, (int, float)) else 0
            progress_updates.append({
                'progress': progress_value,
                'message': message,
                'time': time.time()
            })
            print(f"进度: {progress_value}% - {message}")
        
        # 创建一个测试音频片段
        try:
            # 导入AudioFile
            from app.services.audio_separator import AudioSeparator
            AudioFile = self.separator.AudioFile
            
            # 加载测试音频
            test_wav = AudioFile(self.test_file).read(
                streams=0,
                samplerate=self.config['SAMPLE_RATE'],
                channels=self.config['CHANNELS']
            )
            
            # 裁剪为较小的片段以加快测试
            test_length = min(test_wav.shape[-1], 5 * self.config['SAMPLE_RATE'])  # 最多5秒
            test_wav = test_wav[..., :test_length]
            
            # 添加batch维度
            if len(test_wav.shape) == 2:
                input_wav = test_wav.to(self.separator.device).unsqueeze(0)
            else:
                input_wav = test_wav.to(self.separator.device)
            
            # 测试_apply_model_with_progress函数
            start_time = time.time()
            
            sources = self.separator._apply_model_with_progress(
                model=model,
                mix=input_wav,
                shifts=1,
                split=True,
                overlap=0.25,
                progress=False,
                device=self.separator.device,
                job_id="test-job-id",
                progress_callback=test_callback,
                model_name=model_name
            )
            
            duration = time.time() - start_time
            
            # 验证结果
            self.assertIsNotNone(sources, "apply_model_with_progress返回了None")
            
            # 验证进度更新
            self.assertTrue(len(progress_updates) > 0, "没有进度更新")
            print(f"\n进度更新次数: {len(progress_updates)}")
            print(f"处理时间: {duration:.2f}秒")
            
            # 这个测试只关注是否有任何进度更新，而不检查具体内容
            self.assertTrue(len(progress_updates) > 0, "没有收到任何进度更新")
            
            # 检查第一个更新的进度是否小于最后一个更新的进度
            if len(progress_updates) > 1:
                first_progress = progress_updates[0]['progress']
                last_progress = progress_updates[-1]['progress']
                self.assertTrue(first_progress < last_progress, 
                              f"进度没有增加：从 {first_progress}% 到 {last_progress}%")
            
        except Exception as e:
            self.fail(f"测试apply_model_with_progress时出错: {str(e)}")
        

if __name__ == '__main__':
    unittest.main() 