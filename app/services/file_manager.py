import os
import shutil
import time
import logging
import uuid
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

class FileManager:
    """文件管理服务，负责处理文件上传、清理等操作"""
    
    def __init__(self, app=None):
        self.app = app
        self.upload_folder = None
        self.output_folder = None
        self.file_retention_minutes = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.app = app
        self.upload_folder = app.config['UPLOAD_FOLDER']
        self.output_folder = app.config['OUTPUT_FOLDER']
        self.file_retention_minutes = app.config['FILE_RETENTION_MINUTES']
        
        # 确保目录存在
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
        
        # 启动定期清理任务
        self.start_cleanup_scheduler()
    
    def get_upload_path(self, job_id):
        """获取上传文件的路径"""
        return os.path.join(self.upload_folder, job_id)
    
    def get_output_path(self, job_id):
        """获取输出文件的路径"""
        return os.path.join(self.output_folder, job_id)
    
    def save_uploaded_file(self, file, job_id):
        """保存上传的文件"""
        upload_path = self.get_upload_path(job_id)
        os.makedirs(upload_path, exist_ok=True)
        
        file_path = os.path.join(upload_path, file.filename)
        file.save(file_path)
        
        logger.info(f"已保存文件: {file_path}")
        return file_path
    
    def create_zip_from_directory(self, source_dir, output_path, zip_filename):
        """将目录内容打包为ZIP文件"""
        zip_path = os.path.join(output_path, zip_filename)
        logger.info(f"创建ZIP文件: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # 检查目录是否存在并列出内容
                logger.info(f"源目录中的文件: {os.listdir(source_dir)}")
                
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # 移除基础目录前缀，只保留相对路径
                        arcname = os.path.relpath(src_path, source_dir)
                        logger.info(f"添加文件到ZIP: {src_path} -> {arcname}")
                        zipf.write(src_path, arcname)
            
            # 检查ZIP文件是否成功创建
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                logger.error(f"ZIP文件创建失败或为空: {zip_path}")
                return None
                
            logger.info(f"ZIP文件创建成功: {zip_path}, 大小: {os.path.getsize(zip_path)} 字节")
            return zip_path
        
        except Exception as e:
            logger.error(f"创建ZIP文件时出错: {str(e)}", exc_info=True)
            return None
    
    def cleanup_files(self, cleanup_id):
        """清理特定任务的临时文件"""
        if not cleanup_id or len(cleanup_id) < 32:
            return False, '无效的清理ID'
        
        # 验证ID格式 (UUID格式)
        try:
            uuid.UUID(cleanup_id)
        except ValueError:
            return False, '无效的清理ID格式'
        
        logger.info(f"清理任务ID: {cleanup_id} 的文件")
        
        cleanup_success = False
        
        try:
            # 清理上传目录
            upload_path = os.path.join(self.upload_folder, cleanup_id)
            if os.path.exists(upload_path) and os.path.isdir(upload_path):
                logger.info(f"清理上传目录: {upload_path}")
                shutil.rmtree(upload_path, ignore_errors=True)
                cleanup_success = True
            
            # 清理输出目录
            output_path = os.path.join(self.output_folder, cleanup_id)
            if os.path.exists(output_path) and os.path.isdir(output_path):
                logger.info(f"清理输出目录: {output_path}")
                shutil.rmtree(output_path, ignore_errors=True)
                cleanup_success = True
            
            # 清理分离后的音频目录中对应的文件
            separated_dir = os.path.join(os.getcwd(), 'separated')
            if os.path.exists(separated_dir):
                model_dirs = [os.path.join(separated_dir, d) for d in os.listdir(separated_dir) 
                             if os.path.isdir(os.path.join(separated_dir, d))]
                
                for model_dir in model_dirs:
                    # 尝试找到与任务ID相关的分离音频目录
                    job_related_dirs = []
                    
                    # 查找最近创建的目录（可能与当前任务相关）
                    created_time_range = 60 * 60  # 1小时内创建的目录视为相关
                    now = time.time()
                    
                    for item in os.listdir(model_dir):
                        item_path = os.path.join(model_dir, item)
                        if os.path.isdir(item_path):
                            mtime = os.path.getmtime(item_path)
                            # 如果目录是最近创建的
                            if now - mtime < created_time_range:
                                job_related_dirs.append(item_path)
                    
                    if job_related_dirs:
                        logger.info(f"找到 {len(job_related_dirs)} 个可能相关的分离音频目录")
                        # 仅删除最近的一个目录（最可能是此任务的）
                        newest_dir = max(job_related_dirs, key=os.path.getmtime)
                        logger.info(f"清理分离音频目录: {newest_dir}")
                        shutil.rmtree(newest_dir, ignore_errors=True)
                        cleanup_success = True
            
            if cleanup_success:
                return True, "文件清理成功"
            else:
                return True, "没有找到相关文件"
        
        except Exception as e:
            logger.error(f"清理文件时出错: {str(e)}", exc_info=True)
            return False, f"清理文件时出错: {str(e)}"
    
    def cleanup_old_files(self, retention_minutes=None):
        """清理过期的临时文件和目录"""
        if retention_minutes is None:
            retention_minutes = self.file_retention_minutes
        
        logger.info(f"开始清理超过 {retention_minutes} 分钟的临时文件...")
        
        # 获取当前时间
        now = time.time()
        cutoff_time = now - (retention_minutes * 60)
        
        # 清理上传目录
        self._cleanup_directory(self.upload_folder, cutoff_time)
        
        # 清理输出目录
        self._cleanup_directory(self.output_folder, cutoff_time)
        
        # 清理分离后的音频目录（如果存在）
        separated_dir = os.path.join(os.getcwd(), 'separated')
        if os.path.exists(separated_dir):
            self._cleanup_directory(separated_dir, cutoff_time)
        
        logger.info("清理完成")
    
    def _cleanup_directory(self, directory, cutoff_time):
        """清理指定目录中的过期文件"""
        try:
            if not os.path.exists(directory):
                return
                
            logger.info(f"清理目录: {directory}")
            
            # 列出目录中的所有内容
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                
                # 获取文件/目录的修改时间
                modified_time = os.path.getmtime(item_path)
                
                # 如果文件/目录的修改时间早于截止时间，则删除
                if modified_time < cutoff_time:
                    logger.info(f"删除过期项目: {item_path}")
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
        except Exception as e:
            logger.error(f"清理目录时出错: {str(e)}", exc_info=True)
    
    def start_cleanup_scheduler(self):
        """启动一个后台线程，定期清理过期文件"""
        import threading
        
        def cleanup_task():
            while True:
                try:
                    self.cleanup_old_files()
                except Exception as e:
                    logger.error(f"定期清理任务出错: {str(e)}", exc_info=True)
                
                # 每小时运行一次清理
                time.sleep(3600)
        
        # 创建并启动清理线程
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        logger.info("后台清理任务已启动") 