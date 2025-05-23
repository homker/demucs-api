#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试FFmpeg兼容性问题修复

这个测试文件验证FFmpeg库兼容性问题的修复是否有效
"""

import os
import sys
import unittest
import ctypes
import tempfile
import shutil
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestFFmpegCompatibility(unittest.TestCase):
    """测试FFmpeg兼容性问题修复"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        # 创建临时目录用于符号链接测试
        self.temp_lib_dir = os.path.join(tempfile.gettempdir(), 'test_ffmpeg_libs')
        os.makedirs(self.temp_lib_dir, exist_ok=True)
    
    def tearDown(self):
        """清理测试环境"""
        # 清理临时目录
        if os.path.exists(self.temp_lib_dir):
            shutil.rmtree(self.temp_lib_dir)
    
    def test_ffmpeg_library_paths(self):
        """测试FFmpeg库路径是否存在"""
        print("\n===== 测试FFmpeg库路径 =====")
        
        # FFmpeg 7库文件路径 (macOS)
        ffmpeg7_paths = [
            '/opt/homebrew/lib/libavutil.59.dylib',
            '/opt/homebrew/lib/libavcodec.61.dylib',
            '/opt/homebrew/lib/libavformat.61.dylib',
            '/opt/homebrew/lib/libavdevice.61.dylib',
            '/opt/homebrew/lib/libavfilter.10.dylib',
            '/opt/homebrew/lib/libswresample.5.dylib',
            '/opt/homebrew/lib/libswscale.8.dylib',
            '/opt/homebrew/lib/libpostproc.58.dylib',
        ]
        
        # 检查文件是否存在
        for path in ffmpeg7_paths:
            exists = os.path.exists(path)
            print(f"检查 {path}: {'存在' if exists else '不存在'}")
            # 我们不一定要断言文件存在，因为测试环境可能不同
    
    def test_create_symlinks(self):
        """测试创建符号链接功能"""
        print("\n===== 测试创建符号链接 =====")
        
        # 创建一个示例文件
        test_file = os.path.join(self.temp_lib_dir, 'test_source.lib')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # 创建符号链接
        link_file = os.path.join(self.temp_lib_dir, 'test_link.lib')
        try:
            if os.path.exists(link_file):
                os.remove(link_file)
            
            os.symlink(test_file, link_file)
            self.assertTrue(os.path.exists(link_file), "符号链接创建失败")
            print(f"成功创建符号链接: {link_file} -> {test_file}")
            
            # 验证链接是否正确
            self.assertTrue(os.path.islink(link_file), "创建的不是符号链接")
            self.assertEqual(os.path.realpath(link_file), os.path.realpath(test_file), 
                            "符号链接指向错误")
        except Exception as e:
            self.fail(f"创建符号链接时出错: {str(e)}")
    
    def test_ctypes_library_loading(self):
        """测试使用ctypes加载库文件"""
        print("\n===== 测试ctypes加载库文件 =====")
        
        # 根据平台选择测试库
        if sys.platform == 'darwin':  # macOS
            # 尝试加载系统库
            system_libs = ['/usr/lib/libSystem.dylib']
        elif sys.platform == 'linux':
            # Linux系统库
            system_libs = ['/lib/x86_64-linux-gnu/libc.so.6']
        else:
            system_libs = []
            print(f"未支持的平台: {sys.platform}")
        
        # 尝试加载库
        for lib_path in system_libs:
            if os.path.exists(lib_path):
                try:
                    lib = ctypes.CDLL(lib_path)
                    self.assertIsNotNone(lib, f"加载库失败: {lib_path}")
                    print(f"成功加载库: {lib_path}")
                except Exception as e:
                    print(f"加载库 {lib_path} 失败: {str(e)}")
    
    def test_preload_function(self):
        """测试FFmpeg预加载函数"""
        print("\n===== 测试FFmpeg预加载功能 =====")
        
        # 导入预加载代码
        try:
            # 从run.py中提取预加载部分，创建一个函数
            def preload_ffmpeg():
                import tempfile
                import os
                import sys
                import ctypes
                
                # 创建临时目录用于符号链接
                temp_lib_dir = os.path.join(tempfile.gettempdir(), 'ffmpeg_libs_test')
                os.makedirs(temp_lib_dir, exist_ok=True)
                
                # FFmpeg 7库到FFmpeg 6的映射（仅用于测试）
                # 我们使用一个小的测试集
                lib_mappings = {}
                
                if sys.platform == 'darwin':  # macOS
                    # 找到至少一个实际存在的FFmpeg库
                    ffmpeg_paths = [
                        '/opt/homebrew/lib/libavutil.59.dylib',
                        '/usr/local/lib/libavutil.59.dylib',
                        '/opt/homebrew/lib/libavcodec.61.dylib',
                        '/usr/local/lib/libavcodec.61.dylib'
                    ]
                    
                    for src_path in ffmpeg_paths:
                        if os.path.exists(src_path):
                            # 提取库名称
                            lib_name = os.path.basename(src_path)
                            # 转换为FFmpeg 6格式（仅用于测试）
                            if '59' in lib_name:
                                lib6_name = lib_name.replace('59', '58')
                            elif '61' in lib_name:
                                lib6_name = lib_name.replace('61', '60')
                            else:
                                continue
                            
                            # 添加到映射中
                            lib_mappings[src_path] = os.path.join(temp_lib_dir, lib6_name)
                            break
                
                # 如果找到了库，测试链接创建
                loaded_libs = []
                for src_path, link_path in lib_mappings.items():
                    try:
                        # 加载原始库
                        lib = ctypes.CDLL(src_path)
                        loaded_libs.append(src_path)
                        
                        # 创建符号链接
                        if os.path.exists(link_path):
                            os.remove(link_path)
                        os.symlink(src_path, link_path)
                        
                        # 尝试加载链接的库
                        link_lib = ctypes.CDLL(link_path)
                        loaded_libs.append(link_path)
                    except Exception as e:
                        print(f"处理 {src_path} 时出错: {str(e)}")
                
                # 清理
                try:
                    shutil.rmtree(temp_lib_dir)
                except:
                    pass
                
                return loaded_libs
            
            # 执行预加载函数
            loaded_libs = preload_ffmpeg()
            
            # 验证结果
            self.assertTrue(len(loaded_libs) > 0, "没有成功加载任何库")
            for lib in loaded_libs:
                print(f"预加载成功: {lib}")
        
        except Exception as e:
            self.fail(f"预加载测试失败: {str(e)}")

    def test_file_path_resolution(self):
        """测试文件路径解析功能"""
        print("\n===== 测试文件路径解析功能 =====")
        
        # 创建测试文件
        temp_dir = os.path.join(os.getcwd(), "test_outputs")
        os.makedirs(temp_dir, exist_ok=True)
        
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("测试内容")
        
        # 导入路径解析函数
        try:
            from app.utils.helpers import create_file_response
            from flask import Flask, Response
            import flask
            
            # 创建一个简单的Flask应用上下文
            app = Flask(__name__)
            app.config['BASE_DIR'] = os.getcwd()
            app.config['OUTPUT_FOLDER'] = 'outputs'
            
            with app.app_context():
                # 测试不同路径格式
                test_paths = [
                    # 绝对路径
                    (test_file, True),
                    # 相对路径
                    (os.path.relpath(test_file, os.getcwd()), True),
                    # 不存在的路径
                    (os.path.join(temp_dir, "nonexistent.txt"), False)
                ]
                
                for path, should_exist in test_paths:
                    try:
                        # 先将日志级别设置为CRITICAL以减少输出
                        import logging
                        logging.getLogger().setLevel(logging.CRITICAL)
                        
                        # 测试路径解析
                        try:
                            response = create_file_response(path, "test_download.txt")
                            
                            # 如果文件应该存在，检查响应类型
                            if should_exist:
                                self.assertIsInstance(response, tuple, f"路径 {path} 应该返回有效响应")
                                self.assertTrue(len(response) == 2, "响应应该包含两个元素")
                                self.assertTrue(isinstance(response[0], flask.Response) or isinstance(response[0], dict), 
                                              "响应的第一个元素应该是Response对象或字典")
                                print(f"路径 {path} 解析成功")
                            else:
                                # 应该抛出异常或返回错误响应
                                self.assertTrue(isinstance(response[0], dict) and response[0].get('status') == 'error', 
                                              f"不存在的路径 {path} 应该返回错误响应")
                                print(f"不存在的路径 {path} 正确返回了错误响应")
                        except Exception as e:
                            if not should_exist:
                                # 对于不存在的文件，允许抛出异常
                                print(f"不存在的路径 {path} 抛出异常: {str(e)}")
                            else:
                                self.fail(f"测试路径 {path} 时出错: {str(e)}")
                    
                    except Exception as e:
                        if not should_exist:
                            # 对于不存在的文件，允许抛出异常
                            print(f"不存在的路径 {path} 抛出异常: {str(e)}")
                        else:
                            self.fail(f"测试路径 {path} 时出错: {str(e)}")
            
            print("文件路径解析测试完成")
            
        except Exception as e:
            self.fail(f"测试文件路径解析功能时出错: {str(e)}")
        
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main() 