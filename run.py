import os
import sys
import ctypes
import tempfile
import shutil
from dotenv import load_dotenv

# 预加载FFmpeg库并创建符号链接
try:
    if sys.platform == 'darwin':  # macOS
        # 创建临时目录用于符号链接
        temp_lib_dir = os.path.join(tempfile.gettempdir(), 'ffmpeg_libs')
        os.makedirs(temp_lib_dir, exist_ok=True)
        
        # FFmpeg 7库到FFmpeg 6的映射
        lib_mappings = {
            '/opt/homebrew/lib/libavutil.59.dylib': os.path.join(temp_lib_dir, 'libavutil.58.dylib'),
            '/opt/homebrew/lib/libavcodec.61.dylib': os.path.join(temp_lib_dir, 'libavcodec.60.dylib'),
            '/opt/homebrew/lib/libavformat.61.dylib': os.path.join(temp_lib_dir, 'libavformat.60.dylib'),
            '/opt/homebrew/lib/libavdevice.61.dylib': os.path.join(temp_lib_dir, 'libavdevice.60.dylib'),
            '/opt/homebrew/lib/libavfilter.10.dylib': os.path.join(temp_lib_dir, 'libavfilter.9.dylib'),
            '/opt/homebrew/lib/libswresample.5.dylib': os.path.join(temp_lib_dir, 'libswresample.4.dylib'),
            '/opt/homebrew/lib/libswscale.8.dylib': os.path.join(temp_lib_dir, 'libswscale.7.dylib'),
            '/opt/homebrew/lib/libpostproc.58.dylib': os.path.join(temp_lib_dir, 'libpostproc.57.dylib'),
        }
        
        # 加载FFmpeg库并创建符号链接
        for src_path, link_path in lib_mappings.items():
            try:
                if os.path.exists(src_path):
                    # 加载原始库
                    ctypes.CDLL(src_path)
                    print(f"成功加载 {src_path}")
                    
                    # 创建符号链接
                    if os.path.exists(link_path):
                        os.remove(link_path)
                    os.symlink(src_path, link_path)
                    print(f"创建符号链接: {link_path} -> {src_path}")
                    
                    # 加载链接的库
                    ctypes.CDLL(link_path)
            except Exception as e:
                print(f"处理 {src_path} 时出错: {e}")
        
        # 将临时库目录添加到库搜索路径
        os.environ['DYLD_LIBRARY_PATH'] = f"{temp_lib_dir}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
                
    elif sys.platform == 'linux':  # Linux (Docker环境)
        # Linux环境中的库路径
        ffmpeg_paths = [
            '/usr/local/lib/libavutil.so.58',
            '/usr/local/lib/libavcodec.so.60',
            '/usr/local/lib/libavformat.so.60',
            '/usr/local/lib/libavdevice.so.60',
            '/usr/local/lib/libavfilter.so.9',
            '/usr/local/lib/libswresample.so.4',
            '/usr/local/lib/libswscale.so.7',
            '/usr/local/lib/libpostproc.so.57',
        ]
        for path in ffmpeg_paths:
            try:
                if os.path.exists(path):
                    ctypes.CDLL(path)
                    print(f"成功加载 {path}")
            except Exception as e:
                print(f"加载 {path} 失败: {e}")
except Exception as e:
    print(f"预加载FFmpeg库时出错: {e}")

# 确保可以找到ffprobe
if sys.platform == 'darwin':
    os.environ['PATH'] = f"/opt/homebrew/bin:/usr/local/bin:{os.environ.get('PATH', '')}"
else:
    os.environ['PATH'] = f"/usr/local/bin:{os.environ.get('PATH', '')}"

# 加载.env文件中的环境变量
load_dotenv()

from app import app as application
from app.config import get_config

if __name__ == '__main__':
    config = get_config()
    application.run(
        host=config.HOST,
        port=config.PORT, 
        debug=config.DEBUG,
        use_reloader=False  # 禁用自动重载器，防止生成文件时服务重启
    ) 