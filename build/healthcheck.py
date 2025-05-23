#!/usr/bin/env python
"""
Demucs音频分离系统健康检查脚本
用于监控应用的运行状态和系统资源使用情况
"""

import os
import sys
import json
import time
import argparse
import requests
import psutil
import shutil
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录（脚本在build/目录下）
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# 切换到项目根目录并加载环境变量
os.chdir(PROJECT_ROOT)
load_dotenv()

# 默认配置
DEFAULT_HOST = os.getenv('HOST', '0.0.0.0')
DEFAULT_PORT = int(os.getenv('PORT', 5001))
UPLOADS_DIR = os.getenv('UPLOAD_FOLDER', 'uploads')
OUTPUTS_DIR = os.getenv('OUTPUT_FOLDER', 'outputs')

def check_disk_space(path='.', min_free_gb=5):
    """检查磁盘空间是否足够"""
    total, used, free = shutil.disk_usage(path)
    free_gb = free / (1024 ** 3)  # 转换为GB
    return {
        'total_gb': round(total / (1024 ** 3), 2),
        'used_gb': round(used / (1024 ** 3), 2),
        'free_gb': round(free_gb, 2),
        'healthy': free_gb >= min_free_gb,
        'message': f"可用空间: {round(free_gb, 2)}GB" + (
            "" if free_gb >= min_free_gb else f" (低于最小要求: {min_free_gb}GB)"
        )
    }

def check_api_health(url):
    """检查API是否响应"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                'healthy': True,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'message': f"API响应正常 (响应时间: {round(response_time, 3)}秒)"
            }
        else:
            return {
                'healthy': False,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'message': f"API返回异常状态码: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            'healthy': False,
            'error': str(e),
            'message': f"API请求失败: {str(e)}"
        }

def check_system_resources():
    """检查系统资源使用情况"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    return {
        'cpu': {
            'percent': cpu_percent,
            'healthy': cpu_percent < 90,
            'message': f"CPU使用率: {cpu_percent}%" + (
                "" if cpu_percent < 90 else " (过高)"
            )
        },
        'memory': {
            'total_gb': round(memory.total / (1024 ** 3), 2),
            'used_gb': round(memory.used / (1024 ** 3), 2),
            'percent': memory.percent,
            'healthy': memory.percent < 90,
            'message': f"内存使用率: {memory.percent}%" + (
                "" if memory.percent < 90 else " (过高)"
            )
        }
    }

def check_directories():
    """检查必要的目录是否存在并可写"""
    dirs_to_check = [UPLOADS_DIR, OUTPUTS_DIR]
    results = {}
    
    for dir_path in dirs_to_check:
        exists = os.path.exists(dir_path)
        writable = os.access(dir_path, os.W_OK) if exists else False
        
        results[dir_path] = {
            'exists': exists,
            'writable': writable,
            'healthy': exists and writable,
            'message': (
                f"目录不存在" if not exists else
                f"目录不可写" if not writable else
                "正常"
            )
        }
    
    return results

def check_file_counts():
    """检查上传和输出目录中的文件数量"""
    results = {}
    
    for dir_name, dir_path in [('uploads', UPLOADS_DIR), ('outputs', OUTPUTS_DIR)]:
        if os.path.exists(dir_path):
            file_count = sum(1 for _ in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, _)))
            dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f)))
            
            results[dir_name] = {
                'file_count': file_count,
                'dir_size_mb': round(dir_size / (1024 * 1024), 2),
                'message': f"{file_count}个文件, 总大小: {round(dir_size / (1024 * 1024), 2)}MB"
            }
        else:
            results[dir_name] = {
                'file_count': -1,
                'dir_size_mb': -1,
                'message': "目录不存在"
            }
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Demucs 音频分离系统健康检查工具')
    parser.add_argument('--host', default=DEFAULT_HOST, help=f'API主机地址 (默认: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help=f'API端口 (默认: {DEFAULT_PORT})')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='输出格式 (默认: text)')
    parser.add_argument('--min-free-gb', type=float, default=5, help='最小可用磁盘空间(GB) (默认: 5)')
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    api_url = f"{base_url}/api/models"
    
    # 运行所有检查
    health_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'api': check_api_health(api_url),
        'disk': check_disk_space(min_free_gb=args.min_free_gb),
        'system': check_system_resources(),
        'directories': check_directories(),
        'file_stats': check_file_counts()
    }
    
    # 确定总体健康状态
    overall_healthy = (
        health_data['api'].get('healthy', False) and
        health_data['disk'].get('healthy', False) and
        health_data['system']['cpu'].get('healthy', False) and
        health_data['system']['memory'].get('healthy', False) and
        all(info.get('healthy', False) for info in health_data['directories'].values())
    )
    
    health_data['overall'] = {
        'healthy': overall_healthy,
        'message': "系统状态良好" if overall_healthy else "系统存在问题，请检查详细信息"
    }
    
    # 输出结果
    if args.format == 'json':
        print(json.dumps(health_data, indent=2, ensure_ascii=False))
    else:
        print(f"=== Demucs 音频分离系统健康检查 ({health_data['timestamp']}) ===")
        print(f"总体状态: {'✅ 正常' if overall_healthy else '❌ 异常'}")
        print(f"\n[API] - {health_data['api'].get('message', '未知')}")
        print(f"[磁盘空间] - {health_data['disk'].get('message', '未知')}")
        print(f"[CPU] - {health_data['system']['cpu'].get('message', '未知')}")
        print(f"[内存] - {health_data['system']['memory'].get('message', '未知')}")
        
        print("\n[目录检查]")
        for dir_name, info in health_data['directories'].items():
            status = "✅" if info.get('healthy', False) else "❌"
            print(f"  {status} {dir_name}: {info.get('message', '未知')}")
        
        print("\n[文件统计]")
        for dir_name, info in health_data['file_stats'].items():
            print(f"  - {dir_name}: {info.get('message', '未知')}")
    
    # 如果健康检查失败，返回非零退出码
    if not overall_healthy:
        sys.exit(1)

if __name__ == '__main__':
    main() 