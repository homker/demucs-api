#!/usr/bin/env python3
"""
验证测试重组结果的脚本

检查：
1. 根目录是否已清理旧的测试脚本
2. 新的测试文件是否存在
3. 测试文件是否可以正常导入
4. 测试运行器是否能找到所有测试
"""

import os
import sys
import importlib.util

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (不存在)")
        return False

def check_file_not_exists(file_path, description):
    """检查文件是否已删除"""
    if not os.path.exists(file_path):
        print(f"✅ {description}: {file_path} (已清理)")
        return True
    else:
        print(f"❌ {description}: {file_path} (仍然存在)")
        return False

def check_module_import(module_path, description):
    """检查模块是否可以导入"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", module_path)
        if spec is None:
            print(f"❌ {description}: 无法创建模块规范")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"✅ {description}: 可以正常导入")
        return True
    except Exception as e:
        print(f"❌ {description}: 导入失败 - {e}")
        return False

def main():
    """主验证函数"""
    print("🧪 验证测试重组结果")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # 检查根目录旧文件是否已删除
    print("\n📂 检查根目录清理情况:")
    old_files = [
        "../test_admin_performance.py",
        "../test_api.py", 
        "../test_api_response_format.py",
        "../test_frontend_fix.py"
    ]
    
    for file_path in old_files:
        if check_file_not_exists(file_path, f"已删除旧测试文件"):
            success_count += 1
        total_count += 1
    
    # 检查新的测试文件是否存在
    print("\n📁 检查新测试文件:")
    new_files = [
        ("unit/test_admin_panel.py", "管理面板单元测试"),
        ("unit/test_api.py", "API单元测试"),
        ("integration/test_api_response_format.py", "API响应格式集成测试"),
        ("integration/test_frontend_integration.py", "前端集成测试"),
        ("run_tests.py", "测试运行器")
    ]
    
    for file_path, description in new_files:
        if check_file_exists(file_path, description):
            success_count += 1
        total_count += 1
    
    # 检查模块导入
    print("\n🔧 检查模块导入:")
    import_tests = [
        ("unit/test_admin_panel.py", "管理面板测试模块"),
        ("integration/test_api_response_format.py", "API响应格式测试模块"),
        ("integration/test_frontend_integration.py", "前端集成测试模块")
    ]
    
    for file_path, description in import_tests:
        if os.path.exists(file_path):
            if check_module_import(file_path, description):
                success_count += 1
            total_count += 1
        else:
            print(f"⏭️ {description}: 文件不存在，跳过导入测试")
    
    # 检查测试目录结构
    print("\n🏗️ 检查目录结构:")
    required_dirs = [
        ("unit", "单元测试目录"),
        ("integration", "集成测试目录"),
        ("mcp", "MCP测试目录"),
        ("fixtures", "测试数据目录"),
        ("output", "测试输出目录")
    ]
    
    for dir_path, description in required_dirs:
        if check_file_exists(dir_path, description):
            success_count += 1
        total_count += 1
    
    # 检查关键文件
    print("\n📋 检查关键文件:")
    key_files = [
        ("README.md", "测试目录说明文档"),
        ("TESTING_GUIDE.md", "测试指南"),
        ("run_tests.py", "测试运行脚本")
    ]
    
    for file_path, description in key_files:
        if check_file_exists(file_path, description):
            success_count += 1
        total_count += 1
    
    # 输出总结
    print("\n" + "=" * 50)
    print("🎯 验证结果总结:")
    print(f"✅ 成功项目: {success_count}")
    print(f"❌ 失败项目: {total_count - success_count}")
    print(f"📊 成功率: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 测试重组验证完全通过！")
        print("✨ 所有测试脚本已成功重组到测试目录中")
        
        print("\n💡 使用建议:")
        print("• 运行所有测试: python run_tests.py --test all")
        print("• 运行单元测试: python run_tests.py --category unit") 
        print("• 运行集成测试: python run_tests.py --category integration")
        print("• 查看测试文档: cat README.md")
        
        return True
    else:
        print(f"\n⚠️ 有 {total_count - success_count} 个项目需要修复")
        print("请检查上述失败项目并进行修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 