#!/usr/bin/env python
"""
Demucs音频分离系统自动清理脚本
用于定期清理过期的上传和输出文件，释放磁盘空间
"""

import os
import sys
import time
import shutil
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录（脚本在build/目录下）
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# 切换到项目根目录并加载环境变量
os.chdir(PROJECT_ROOT)
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup.log')
    ]
)
logger = logging.getLogger('file_cleanup')

# 默认配置
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'outputs')
FILE_RETENTION_MINUTES = int(os.getenv('FILE_RETENTION_MINUTES', 60))

def get_file_stats(directory):
    """获取目录中的文件统计信息"""
    if not os.path.exists(directory):
        return {"files": 0, "size": 0}
    
    total_files = 0
    total_size = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                total_files += 1
                total_size += os.path.getsize(file_path)
    
    return {
        "files": total_files,
        "size": total_size,
        "size_mb": round(total_size / (1024 * 1024), 2)
    }

def cleanup_old_files(directory, minutes=FILE_RETENTION_MINUTES, dry_run=False):
    """清理超过指定时间的文件"""
    if not os.path.exists(directory):
        logger.warning(f"目录不存在: {directory}")
        return {"deleted_files": 0, "deleted_size": 0}
    
    cutoff_time = time.time() - (minutes * 60)
    deleted_files = 0
    deleted_size = 0
    
    logger.info(f"开始清理 {directory} 中超过 {minutes} 分钟的文件...")
    
    for root, dirs, files in os.walk(directory, topdown=False):
        # 首先处理文件
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    file_size = os.path.getsize(file_path)
                    if not dry_run:
                        try:
                            os.remove(file_path)
                            deleted_files += 1
                            deleted_size += file_size
                            logger.debug(f"已删除: {file_path}")
                        except Exception as e:
                            logger.error(f"删除文件时出错 {file_path}: {e}")
                    else:
                        deleted_files += 1
                        deleted_size += file_size
                        logger.debug(f"将被删除: {file_path}")
        
        # 然后处理空目录
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if os.path.isdir(dir_path) and not os.listdir(dir_path):
                if not dry_run:
                    try:
                        os.rmdir(dir_path)
                        logger.debug(f"已删除空目录: {dir_path}")
                    except Exception as e:
                        logger.error(f"删除目录时出错 {dir_path}: {e}")
                else:
                    logger.debug(f"将被删除的空目录: {dir_path}")
    
    return {
        "deleted_files": deleted_files,
        "deleted_size": deleted_size,
        "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
    }

def main():
    parser = argparse.ArgumentParser(description='Demucs音频分离系统文件清理工具')
    parser.add_argument('--minutes', type=int, default=FILE_RETENTION_MINUTES,
                        help=f'保留文件的分钟数 (默认: {FILE_RETENTION_MINUTES})')
    parser.add_argument('--dry-run', action='store_true',
                        help='模拟运行，不实际删除文件')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='启用详细日志输出')
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 开始时间
    start_time = datetime.now()
    logger.info(f"开始文件清理任务 (保留 {args.minutes} 分钟内的文件)...")
    
    if args.dry_run:
        logger.info("模拟运行模式，不会实际删除文件")
    
    # 获取清理前的统计信息
    before_stats = {
        "uploads": get_file_stats(UPLOAD_FOLDER),
        "outputs": get_file_stats(OUTPUT_FOLDER)
    }
    logger.info(f"清理前 - 上传目录: {before_stats['uploads']['files']}个文件, "
                f"{before_stats['uploads']['size_mb']}MB; "
                f"输出目录: {before_stats['outputs']['files']}个文件, "
                f"{before_stats['outputs']['size_mb']}MB")
    
    # 执行清理
    upload_results = cleanup_old_files(UPLOAD_FOLDER, args.minutes, args.dry_run)
    output_results = cleanup_old_files(OUTPUT_FOLDER, args.minutes, args.dry_run)
    
    # 获取清理后的统计信息
    after_stats = {
        "uploads": get_file_stats(UPLOAD_FOLDER),
        "outputs": get_file_stats(OUTPUT_FOLDER)
    }
    
    # 计算总共删除的数据
    total_deleted_files = upload_results["deleted_files"] + output_results["deleted_files"]
    total_deleted_mb = upload_results["deleted_size_mb"] + output_results["deleted_size_mb"]
    
    # 清理总结
    logger.info(f"清理完成! 总共删除了 {total_deleted_files} 个文件, {total_deleted_mb}MB")
    logger.info(f"上传目录: 删除了 {upload_results['deleted_files']}个文件, {upload_results['deleted_size_mb']}MB")
    logger.info(f"输出目录: 删除了 {output_results['deleted_files']}个文件, {output_results['deleted_size_mb']}MB")
    logger.info(f"清理后 - 上传目录: {after_stats['uploads']['files']}个文件, "
                f"{after_stats['uploads']['size_mb']}MB; "
                f"输出目录: {after_stats['outputs']['files']}个文件, "
                f"{after_stats['outputs']['size_mb']}MB")
    
    # 完成时间
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"清理任务完成，耗时: {duration:.2f}秒")

if __name__ == '__main__':
    main() 