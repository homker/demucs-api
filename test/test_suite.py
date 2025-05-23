#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试套件管理脚本

提供测试发现、组织和运行的高级接口
"""

import os
import sys
import unittest
import importlib
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSuiteManager:
    """测试套件管理器"""
    
    def __init__(self, base_dir=None):
        """初始化测试套件管理器
        
        Args:
            base_dir: 测试目录基础路径，默认为当前文件所在目录
        """
        self.base_dir = base_dir or Path(__file__).parent
        self.test_modules = {}
        self.discover_tests()
    
    def discover_tests(self):
        """自动发现测试模块"""
        print("🔍 正在发现测试模块...")
        
        # 发现单元测试
        unit_dir = self.base_dir / "unit"
        if unit_dir.exists():
            self.test_modules['unit'] = self._discover_in_directory(unit_dir, "unit")
        
        # 发现集成测试
        integration_dir = self.base_dir / "integration"
        if integration_dir.exists():
            self.test_modules['integration'] = self._discover_in_directory(integration_dir, "integration")
        
        # 发现MCP测试
        mcp_dir = self.base_dir / "mcp"
        if mcp_dir.exists():
            self.test_modules['mcp'] = self._discover_in_directory(mcp_dir, "mcp")
        
        # 打印发现结果
        for category, modules in self.test_modules.items():
            print(f"📁 {category}: 发现 {len(modules)} 个测试模块")
            for module_name in modules:
                print(f"   - {module_name}")
    
    def _discover_in_directory(self, directory, package_name):
        """在指定目录中发现测试模块"""
        test_files = []
        
        for file_path in directory.glob("test_*.py"):
            module_name = file_path.stem
            if module_name != "__init__":
                test_files.append(f"{package_name}.{module_name}")
        
        return test_files
    
    def load_test_suite(self, category=None, test_name=None):
        """加载测试套件
        
        Args:
            category: 测试类别 ('unit', 'integration', 'mcp')
            test_name: 特定测试名称
            
        Returns:
            unittest.TestSuite
        """
        suite = unittest.TestSuite()
        
        if category and category in self.test_modules:
            categories = [category]
        else:
            categories = self.test_modules.keys()
        
        for cat in categories:
            for module_name in self.test_modules.get(cat, []):
                try:
                    # 如果指定了测试名称，只加载匹配的模块
                    if test_name and test_name not in module_name:
                        continue
                    
                    # 动态导入测试模块
                    module = importlib.import_module(module_name)
                    
                    # 加载模块中的所有测试用例
                    loader = unittest.TestLoader()
                    module_suite = loader.loadTestsFromModule(module)
                    suite.addTest(module_suite)
                    
                    print(f"✅ 加载测试模块: {module_name}")
                    
                except ImportError as e:
                    print(f"❌ 无法导入测试模块 {module_name}: {e}")
                except Exception as e:
                    print(f"⚠️ 加载测试模块 {module_name} 时出错: {e}")
        
        return suite
    
    def run_tests(self, category=None, test_name=None, verbosity=2):
        """运行测试
        
        Args:
            category: 测试类别
            test_name: 特定测试名称
            verbosity: 详细程度 (0-2)
            
        Returns:
            bool: 测试是否全部通过
        """
        print("🧪 开始运行测试...")
        print("="*60)
        
        # 加载测试套件
        suite = self.load_test_suite(category, test_name)
        
        if suite.countTestCases() == 0:
            print("⚠️ 没有找到任何测试用例")
            return True
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        
        # 打印测试总结
        self._print_test_summary(result)
        
        return result.wasSuccessful()
    
    def _print_test_summary(self, result):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 测试执行总结")
        print("="*60)
        
        print(f"🔢 运行测试数: {result.testsRun}")
        print(f"✅ 成功测试数: {result.testsRun - len(result.failures) - len(result.errors)}")
        print(f"❌ 失败测试数: {len(result.failures)}")
        print(f"🔴 错误测试数: {len(result.errors)}")
        
        if hasattr(result, 'skipped'):
            print(f"🟡 跳过测试数: {len(result.skipped)}")
        
        # 显示失败的测试
        if result.failures:
            print("\n❌ 失败的测试:")
            for test, traceback in result.failures:
                print(f"   - {test.id()}")
        
        # 显示错误的测试
        if result.errors:
            print("\n🔴 错误的测试:")
            for test, traceback in result.errors:
                print(f"   - {test.id()}")
        
        # 显示跳过的测试
        if hasattr(result, 'skipped') and result.skipped:
            print("\n🟡 跳过的测试:")
            for test, reason in result.skipped:
                print(f"   - {test.id()}: {reason}")
        
        # 最终结果
        if result.wasSuccessful():
            print("\n🎉 所有测试通过!")
        else:
            failed_count = len(result.failures) + len(result.errors)
            print(f"\n⚠️ 有 {failed_count} 个测试失败或出错")
    
    def list_tests(self):
        """列出所有可用的测试"""
        print("📋 可用的测试模块:")
        print("="*60)
        
        for category, modules in self.test_modules.items():
            print(f"\n📁 {category.upper()}:")
            for module_name in modules:
                print(f"   - {module_name}")
        
        print(f"\n🔢 总计: {sum(len(modules) for modules in self.test_modules.values())} 个测试模块")
    
    def validate_environment(self):
        """验证测试环境"""
        print("🔧 验证测试环境...")
        
        issues = []
        
        # 检查测试音频文件
        test_audio = self.base_dir / "test.mp3"
        if not test_audio.exists():
            issues.append("❌ 缺少测试音频文件: test.mp3")
        else:
            print("✅ 测试音频文件存在")
        
        # 检查依赖
        required_packages = ['torch', 'torchaudio', 'demucs', 'flask', 'requests']
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✅ {package} 已安装")
            except ImportError:
                issues.append(f"❌ 缺少依赖包: {package}")
        
        # 检查测试目录结构
        for category in ['unit', 'integration', 'mcp']:
            test_dir = self.base_dir / category
            if test_dir.exists():
                print(f"✅ {category} 目录存在")
            else:
                issues.append(f"⚠️ {category} 目录不存在")
        
        if issues:
            print("\n🚨 发现环境问题:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print("\n🎉 测试环境验证通过!")
            return True

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="测试套件管理脚本")
    parser.add_argument('--action', choices=['run', 'list', 'validate'], 
                        default='run', help='执行的操作')
    parser.add_argument('--category', choices=['unit', 'integration', 'mcp'], 
                        help='测试类别')
    parser.add_argument('--test', help='特定测试名称')
    parser.add_argument('--verbosity', type=int, choices=[0, 1, 2], 
                        default=2, help='详细程度')
    
    args = parser.parse_args()
    
    # 创建测试套件管理器
    manager = TestSuiteManager()
    
    # 执行相应操作
    if args.action == 'list':
        manager.list_tests()
    elif args.action == 'validate':
        success = manager.validate_environment()
        sys.exit(0 if success else 1)
    else:  # run
        success = manager.run_tests(args.category, args.test, args.verbosity)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 