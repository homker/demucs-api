#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本

用于快速验证Demucs音频分离应用的基本功能
适合新手和快速验证场景
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_header(title):
    """打印测试标题"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status} - {test_name}")
    if message:
        print(f"    {message}")

def test_environment():
    """测试环境检查"""
    print_header("环境检查")
    
    all_passed = True
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 7):
        print_result("Python版本", True, f"Python {python_version.major}.{python_version.minor}")
    else:
        print_result("Python版本", False, f"需要Python 3.7+，当前: {python_version.major}.{python_version.minor}")
        all_passed = False
    
    # 检查依赖包
    required_packages = ['torch', 'torchaudio', 'demucs', 'flask', 'requests']
    
    for package in required_packages:
        try:
            __import__(package)
            print_result(f"依赖包 {package}", True)
        except ImportError:
            print_result(f"依赖包 {package}", False, "未安装")
            all_passed = False
    
    # 检查测试音频文件
    test_audio = Path(__file__).parent / "test.mp3"
    if test_audio.exists():
        file_size = test_audio.stat().st_size
        print_result("测试音频文件", True, f"大小: {file_size//1024}KB")
    else:
        print_result("测试音频文件", False, "test.mp3 不存在")
        all_passed = False
    
    return all_passed

def test_basic_imports():
    """测试基本导入"""
    print_header("基本功能导入测试")
    
    all_passed = True
    
    # 测试应用模块导入
    try:
        from app.factory import create_app
        print_result("Flask应用工厂", True)
    except Exception as e:
        print_result("Flask应用工厂", False, str(e))
        all_passed = False
    
    try:
        from app.services.audio_separator import AudioSeparator
        print_result("音频分离器", True)
    except Exception as e:
        print_result("音频分离器", False, str(e))
        all_passed = False
    
    try:
        from app.services.file_manager import FileManager
        print_result("文件管理器", True)
    except Exception as e:
        print_result("文件管理器", False, str(e))
        all_passed = False
    
    return all_passed

def test_model_loading():
    """测试模型加载"""
    print_header("模型加载测试")
    
    try:
        from app.config import Config
        from app.services.audio_separator import AudioSeparator
        
        print("📥 正在初始化音频分离器...")
        config = Config()
        separator = AudioSeparator(config)
        
        print("📋 获取可用模型...")
        models = separator.get_available_models()
        
        if models:
            print_result("模型加载", True, f"可用模型: {', '.join(models)}")
            return True
        else:
            print_result("模型加载", False, "未找到可用模型")
            return False
            
    except Exception as e:
        print_result("模型加载", False, str(e))
        return False

def test_api_server():
    """测试API服务器连接"""
    print_header("API服务器连接测试")
    
    try:
        import requests
        
        # 测试服务器连接
        response = requests.get("http://127.0.0.1:8080/api/models", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', {}).get('models', [])
            print_result("API服务器连接", True, f"发现 {len(models)} 个模型")
            return True
        else:
            print_result("API服务器连接", False, f"HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_result("API服务器连接", False, "无法连接 (服务器可能未启动)")
        return False
    except Exception as e:
        print_result("API服务器连接", False, str(e))
        return False

def test_basic_audio_processing():
    """测试基本音频处理"""
    print_header("基本音频处理测试")
    
    test_audio = Path(__file__).parent / "test.mp3"
    if not test_audio.exists():
        print_result("音频处理测试", False, "测试音频文件不存在")
        return False
    
    try:
        from app.config import Config
        from app.services.audio_separator import AudioSeparator
        
        config = Config()
        separator = AudioSeparator(config)
        
        # 创建临时输出目录
        with tempfile.TemporaryDirectory() as temp_dir:
            print("🎵 正在处理测试音频...")
            
            start_time = time.time()
            
            # 测试分离功能
            result = separator.separate_track(
                input_file=str(test_audio),
                output_dir=temp_dir,
                model_name="htdemucs",
                stems=["vocals"],  # 只分离人声，加快测试速度
                progress_callback=None
            )
            
            process_time = time.time() - start_time
            
            if result and 'files' in result and len(result['files']) > 0:
                output_file = result['files'][0]['path']
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print_result("音频处理测试", True, 
                               f"处理时间: {process_time:.1f}秒, 输出大小: {file_size//1024}KB")
                    return True
                else:
                    print_result("音频处理测试", False, "输出文件未生成")
                    return False
            else:
                print_result("音频处理测试", False, "处理结果为空")
                return False
                
    except Exception as e:
        print_result("音频处理测试", False, str(e))
        return False

def main():
    """主测试函数"""
    print("🚀 Demucs音频分离应用 - 快速测试")
    print("📍 工作目录:", os.getcwd())
    
    start_time = time.time()
    test_results = []
    
    # 运行测试
    test_results.append(("环境检查", test_environment()))
    test_results.append(("基本导入", test_basic_imports()))
    test_results.append(("模型加载", test_model_loading()))
    test_results.append(("API服务器", test_api_server()))
    test_results.append(("音频处理", test_basic_audio_processing()))
    
    # 统计结果
    total_time = time.time() - start_time
    passed_tests = sum(1 for _, passed in test_results if passed)
    total_tests = len(test_results)
    
    # 打印总结
    print_header("测试总结")
    print(f"⏱️  总耗时: {total_time:.1f} 秒")
    print(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    print(f"🎯 成功率: {passed_tests/total_tests*100:.1f}%")
    
    print("\n📋 详细结果:")
    for test_name, passed in test_results:
        status = "✅" if passed else "❌"
        print(f"   {status} {test_name}")
    
    # 建议
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过! 系统运行正常。")
        print("\n📚 下一步:")
        print("   - 运行完整测试: python test/test_suite.py")
        print("   - 查看测试指南: test/TESTING_GUIDE.md")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败。")
        print("\n🔧 建议修复:")
        
        for test_name, passed in test_results:
            if not passed:
                if test_name == "环境检查":
                    print("   - 安装缺失的依赖: pip install -r requirements.txt")
                    print("   - 检查Python版本是否 >= 3.7")
                elif test_name == "API服务器":
                    print("   - 启动应用服务器: python run.py")
                elif test_name == "音频处理":
                    print("   - 确保有足够内存和存储空间")
                    print("   - 检查音频文件格式是否支持")
        
        print("\n📚 获取帮助:")
        print("   - 查看故障排除指南: test/TESTING_GUIDE.md")
        print("   - 运行环境验证: python test/test_suite.py --action validate")
    
    # 设置退出代码
    return 0 if passed_tests == total_tests else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 