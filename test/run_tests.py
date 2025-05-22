#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

使用方法:
python run_tests.py [--test <test_type>]

参数:
--test: 指定要运行的测试类型
    ffmpeg: 运行FFmpeg兼容性测试
    progress: 运行进度反馈测试
    api: 运行API接口测试
    all: 运行所有测试 (默认)
"""

import unittest
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests(test_type="all"):
    """根据指定类型运行测试"""
    
    # 加载测试模块
    if test_type == "ffmpeg":
        from test_ffmpeg_compatibility import TestFFmpegCompatibility
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestFFmpegCompatibility)
        print("=== 运行FFmpeg兼容性测试 ===")
    elif test_type == "progress":
        from test_progress_feedback import TestProgressFeedback
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestProgressFeedback)
        print("=== 运行进度反馈测试 ===")
    elif test_type == "api":
        from test_api import APITest
        test_suite = unittest.TestLoader().loadTestsFromTestCase(APITest)
        print("=== 运行API接口测试 ===")
    else:  # all
        # 加载所有测试模块
        from test_ffmpeg_compatibility import TestFFmpegCompatibility
        from test_progress_feedback import TestProgressFeedback
        try:
            from test_api import APITest
            test_suite = unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestFFmpegCompatibility),
                unittest.TestLoader().loadTestsFromTestCase(TestProgressFeedback),
                unittest.TestLoader().loadTestsFromTestCase(APITest)
            ])
        except ImportError:
            # API测试可能不存在
            test_suite = unittest.TestSuite([
                unittest.TestLoader().loadTestsFromTestCase(TestFFmpegCompatibility),
                unittest.TestLoader().loadTestsFromTestCase(TestProgressFeedback)
            ])
        print("=== 运行所有测试 ===")
    
    # 运行测试
    result = unittest.TextTestRunner().run(test_suite)
    
    # 返回测试结果，用于退出代码
    return result.wasSuccessful()

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行音频分离应用测试")
    parser.add_argument('--test', type=str, choices=['ffmpeg', 'progress', 'api', 'all'],
                        default='all', help='指定要运行的测试类型')
    
    args = parser.parse_args()
    
    # 运行测试
    success = run_tests(args.test)
    
    # 设置退出代码
    sys.exit(0 if success else 1) 