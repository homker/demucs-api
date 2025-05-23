#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

使用方法:
python run_tests.py [--test <test_type>] [--category <category>] [--mode <mode>]

参数:
--test: 指定要运行的测试类型
    ffmpeg: 运行FFmpeg兼容性测试
    progress: 运行进度反馈测试
    api: 运行API接口测试
    download: 运行下载功能测试
    admin: 运行管理面板测试
    format: 运行音频格式和质量测试
    demucs: 运行Demucs核心功能测试
    separator: 运行音频分离器测试
    full: 运行完整应用测试
    all: 运行所有测试 (默认)

--category: 指定要运行的测试类别
    unit: 运行单元测试
    integration: 运行集成测试
    mcp: 运行MCP协议测试
    all: 运行所有类别测试 (默认)

--mode: 指定测试模式 (仅对format测试有效)
    fast: 快速模式，只测试WAV和MP3格式 (默认)
    full: 完整模式，包含耗时的FLAC无损测试
"""

import unittest
import argparse
import sys
import os
import subprocess
import json
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_details': []
        }
        
    def run_command(self, command, description, timeout=60):
        """运行命令并记录结果"""
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"命令: {command}")
        print('='*60)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            test_result = {
                'name': description,
                'command': command,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time,
                'status': 'passed' if result.returncode == 0 else 'failed'
            }
            
            self.results['test_details'].append(test_result)
            self.results['total_tests'] += 1
            
            if result.returncode == 0:
                print(f"✅ {description} - 通过")
                self.results['passed_tests'] += 1
            else:
                print(f"❌ {description} - 失败")
                print(f"错误输出: {result.stderr}")
                self.results['failed_tests'] += 1
                
            print(f"输出: {result.stdout}")
            print(f"执行时间: {execution_time:.2f}秒")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - 超时")
            self.results['test_details'].append({
                'name': description,
                'command': command,
                'status': 'timeout',
                'execution_time': timeout
            })
            self.results['total_tests'] += 1
            self.results['failed_tests'] += 1
            return False
            
        except Exception as e:
            print(f"💥 {description} - 异常: {e}")
            self.results['test_details'].append({
                'name': description,
                'command': command,
                'status': 'error',
                'error': str(e)
            })
            self.results['total_tests'] += 1
            self.results['failed_tests'] += 1
            return False
    
    def run_basic_tests(self):
        """运行基础功能测试"""
        print("\n🔧 基础功能测试")
        
        # 检查Python环境和依赖
        self.run_command(
            "python --version",
            "Python版本检查"
        )
        
        self.run_command(
            "pip list | grep -E '(flask|requests|torch)'",
            "关键依赖检查"
        )
        
        # 检查项目文件结构
        self.run_command(
            "ls -la ../app/",
            "项目结构检查"
        )
    
    def run_api_tests(self):
        """运行API测试"""
        print("\n🌐 API接口测试")
        
        # 格式和质量快速测试
        if os.path.exists("test/test_format_quality_quick.py"):
            self.run_command(
                "cd .. && python test/test_format_quality_quick.py",
                "格式和质量API测试",
                timeout=120
            )
        
    def run_admin_tests(self):
        """运行管理功能测试"""
        print("\n🛠️ 管理功能测试")
        
        # 任务视图测试
        if os.path.exists("test/test_task_view.py"):
            self.run_command(
                "cd .. && python test/test_task_view.py",
                "任务管理功能测试",
                timeout=90
            )
    
    def run_integration_tests(self):
        """运行集成测试"""
        print("=== 运行集成测试 ===")
        
        success = True
        
        # 运行API响应格式测试
        try:
            from integration.test_api_response_format import run_api_response_format_tests
            print("🧪 运行API响应格式测试...")
            if not run_api_response_format_tests():
                success = False
        except ImportError as e:
            print(f"⚠️ API响应格式测试模块无法导入: {e}")
        except Exception as e:
            print(f"❌ API响应格式测试执行失败: {e}")
            success = False
        
        # 运行前端集成测试
        try:
            from integration.test_frontend_integration import run_frontend_integration_tests
            print("🧪 运行前端集成测试...")
            if not run_frontend_integration_tests():
                success = False
        except ImportError as e:
            print(f"⚠️ 前端集成测试模块无法导入: {e}")
        except Exception as e:
            print(f"❌ 前端集成测试执行失败: {e}")
            success = False
        
        if success:
            print("✅ 所有集成测试通过")
        else:
            print("❌ 部分集成测试失败")
        
        return success
    
    def run_frontend_tests(self):
        """运行前端测试"""
        print("\n🎨 前端测试")
        
        # 检查模板文件
        templates = [
            "app/templates/index.html",
            "app/templates/docs.html",
            "app/templates/test.html",
            "app/templates/admin.html",
            "app/templates/admin_login.html"
        ]
        
        for template in templates:
            if os.path.exists(f"../{template}"):
                self.run_command(
                    f"wc -l ../{template}",
                    f"模板文件检查: {template}"
                )
        
        # 检查静态资源
        static_files = [
            "app/static/css/main.css",
            "app/static/js/main.js"
        ]
        
        for static_file in static_files:
            if os.path.exists(f"../{static_file}"):
                self.run_command(
                    f"ls -la ../{static_file}",
                    f"静态文件检查: {static_file}"
                )
    
    def generate_report(self, output_file=None):
        """生成测试报告"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_report_{timestamp}.json"
        
        # 计算成功率
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
        else:
            success_rate = 0
        
        self.results['success_rate'] = success_rate
        
        # 保存JSON报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        # 生成文本摘要
        summary_file = output_file.replace('.json', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Demucs 测试报告摘要\n")
            f.write("="*50 + "\n")
            f.write(f"测试时间: {self.results['timestamp']}\n")
            f.write(f"总测试数: {self.results['total_tests']}\n")
            f.write(f"通过: {self.results['passed_tests']}\n")
            f.write(f"失败: {self.results['failed_tests']}\n")
            f.write(f"跳过: {self.results['skipped_tests']}\n")
            f.write(f"成功率: {success_rate:.1f}%\n")
            f.write("\n详细结果:\n")
            f.write("-"*50 + "\n")
            
            for test in self.results['test_details']:
                status_icon = "✅" if test['status'] == 'passed' else "❌"
                f.write(f"{status_icon} {test['name']}\n")
                if 'execution_time' in test:
                    f.write(f"   执行时间: {test['execution_time']:.2f}秒\n")
                if test['status'] != 'passed' and 'stderr' in test:
                    f.write(f"   错误: {test['stderr'][:100]}...\n")
                f.write("\n")
        
        print(f"\n📊 测试报告已生成:")
        print(f"   详细报告: {output_file}")
        print(f"   摘要报告: {summary_file}")
        
        return output_file
    
    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{'='*60}")
        print("🎯 测试总结")
        print('='*60)
        print(f"总测试数: {self.results['total_tests']}")
        print(f"✅ 通过: {self.results['passed_tests']}")
        print(f"❌ 失败: {self.results['failed_tests']}")
        print(f"⏭️ 跳过: {self.results['skipped_tests']}")
        
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
            print(f"📈 成功率: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 测试结果优秀!")
            elif success_rate >= 70:
                print("👍 测试结果良好!")
            elif success_rate >= 50:
                print("⚠️ 测试结果一般，建议检查失败的测试")
            else:
                print("🔥 测试结果不佳，需要紧急修复")
        
        print('='*60)

def run_unit_tests(test_category="all", mode="fast"):
    """运行单元测试"""
    print("=== 运行单元测试 ===")
    
    if test_category == "all":
        try:
            from unit.test_audio_format_quality import run_format_quality_tests
            run_format_quality_tests()
        except ImportError as e:
            print(f"⚠️ 格式质量测试模块无法导入: {e}")
        
        try:
            from unit.test_admin_panel import run_admin_tests
            run_admin_tests()
        except ImportError as e:
            print(f"⚠️ 管理面板测试模块无法导入: {e}")
        
        try:
            from unit.test_download_functionality import run_download_tests
            run_download_tests()
        except ImportError as e:
            print(f"⚠️ 下载功能测试模块无法导入: {e}")
            
    elif test_category == "format":
        if mode == "fast":
            try:
                from unit.test_audio_format_quality import run_format_quality_tests
                print("🚀 运行快速格式测试 (只测试WAV和MP3)")
                return run_format_quality_tests()
            except ImportError as e:
                print(f"⚠️ 快速格式质量测试模块无法导入: {e}")
                return False
        elif mode == "full":
            try:
                from unit.test_audio_format_quality_full import run_format_quality_full_tests
                print("🐌 运行完整格式测试 (包含FLAC无损测试)")
                return run_format_quality_full_tests()
            except ImportError as e:
                print(f"⚠️ 完整格式质量测试模块无法导入: {e}")
                return False
    
    elif test_category == "admin":
        try:
            from unit.test_admin_panel import run_admin_tests
            return run_admin_tests()
        except ImportError as e:
            print(f"⚠️ 管理面板测试模块无法导入: {e}")
            return False
            
    elif test_category == "download":
        try:
            from unit.test_download_functionality import run_download_tests
            return run_download_tests()
        except ImportError as e:
            print(f"⚠️ 下载功能测试模块无法导入: {e}")
            return False
    
    return True

def run_mcp_tests():
    """运行MCP协议测试"""
    print("=== 运行MCP协议测试 ===")
    test_suite = unittest.TestSuite()
    
    try:
        from mcp.client import MCPClientTest
        test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(MCPClientTest))
    except ImportError as e:
        print(f"⚠️ MCP测试模块无法导入: {e}")
    
    return test_suite

def run_integration_tests():
    """运行集成测试"""
    print("=== 运行集成测试 ===")
    
    success = True
    
    # 运行API响应格式测试
    try:
        from integration.test_api_response_format import run_api_response_format_tests
        print("🧪 运行API响应格式测试...")
        if not run_api_response_format_tests():
            success = False
    except ImportError as e:
        print(f"⚠️ API响应格式测试模块无法导入: {e}")
    except Exception as e:
        print(f"❌ API响应格式测试执行失败: {e}")
        success = False
    
    # 运行前端集成测试
    try:
        from integration.test_frontend_integration import run_frontend_integration_tests
        print("🧪 运行前端集成测试...")
        if not run_frontend_integration_tests():
            success = False
    except ImportError as e:
        print(f"⚠️ 前端集成测试模块无法导入: {e}")
    except Exception as e:
        print(f"❌ 前端集成测试执行失败: {e}")
        success = False
    
    if success:
        print("✅ 所有集成测试通过")
    else:
        print("❌ 部分集成测试失败")
    
    return success

def run_tests(test_type="all", category="all", mode="fast"):
    """根据指定类型和类别运行测试"""
    
    test_suite = unittest.TestSuite()
    
    if category == "unit":
        test_suite.addTest(run_unit_tests(test_type, mode))
    elif category == "integration":
        test_suite.addTest(run_integration_tests())
    elif category == "mcp":
        test_suite.addTest(run_mcp_tests())
    else:  # all categories
        test_suite.addTest(run_unit_tests(test_type, mode))
        test_suite.addTest(run_integration_tests())
        test_suite.addTest(run_mcp_tests())
    
    # 运行测试
    print("\n" + "="*60)
    print("开始执行测试...")
    print("="*60)
    
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    
    # 输出测试总结
    print("\n" + "="*60)
    print("测试执行完成")
    print("="*60)
    print(f"运行测试数: {result.testsRun}")
    print(f"失败测试数: {len(result.failures)}")
    print(f"错误测试数: {len(result.errors)}")
    print(f"跳过测试数: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n🔴 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.wasSuccessful():
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️ 有 {len(result.failures) + len(result.errors)} 个测试失败或出错")
    
    # 返回测试结果，用于退出代码
    return result.wasSuccessful()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Demucs 测试运行器")
    parser.add_argument('--test', choices=['basic', 'api', 'admin', 'integration', 'frontend', 'all'], 
                       default='all', help='选择要运行的测试类型')
    parser.add_argument('--output', help='测试报告输出文件名')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    print("🚀 Demucs 测试运行器启动")
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 根据参数运行不同的测试
    if args.test == 'all' or args.test == 'basic':
        runner.run_basic_tests()
    
    if args.test == 'all' or args.test == 'api':
        runner.run_api_tests()
    
    if args.test == 'all' or args.test == 'admin':
        runner.run_admin_tests()
    
    if args.test == 'all' or args.test == 'integration':
        runner.run_integration_tests()
    
    if args.test == 'all' or args.test == 'frontend':
        runner.run_frontend_tests()
    
    # 生成报告
    runner.generate_report(args.output)
    runner.print_summary()
    
    # 返回适当的退出码
    if runner.results['failed_tests'] == 0:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print(f"\n💥 有 {runner.results['failed_tests']} 个测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main() 