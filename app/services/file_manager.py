import os
import shutil
import time
import logging
import uuid
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

class FileManager:
    """File management service for handling file uploads, cleaning, etc."""
    
    def __init__(self, config):
        self.config = config
        self.upload_folder = config['UPLOAD_FOLDER']
        self.output_folder = config['OUTPUT_FOLDER']
        self.file_retention_minutes = config['FILE_RETENTION_MINUTES']
        
        # Ensure directories exist
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.output_folder, exist_ok=True)
    
    def get_upload_path(self, job_id):
        """Get upload file path"""
        return os.path.join(self.upload_folder, job_id)
    
    def get_output_path(self, job_id):
        """Get output file path"""
        return os.path.join(self.output_folder, job_id)
    
    def save_uploaded_file(self, file, filename: Optional[str] = None) -> Tuple[str, str]:
        """
        Save an uploaded file to the upload directory
        
        Args:
            file: File object from request
            filename: Optional custom filename
            
        Returns:
            Tuple of (filename, file_path)
        """
        if not file:
            raise ValueError("No file provided")
            
        if filename is None:
            # Generate unique filename if not provided
            original_filename = file.filename
            name_parts = os.path.splitext(original_filename)
            safe_filename = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}{name_parts[1]}"
        else:
            safe_filename = filename
            
        file_path = os.path.join(self.upload_folder, safe_filename)
        file.save(file_path)
        logger.info(f"Saved uploaded file: {file_path}")
        
        return safe_filename, file_path
    
    def create_job_output_directory(self, job_id: str) -> str:
        """
        Create a directory for a specific job's output files
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path to the job output directory
        """
        # Create dated folder for better organization
        date_str = datetime.now().strftime("%Y%m%d")
        job_dir = os.path.join(self.output_folder, date_str, job_id)
        os.makedirs(job_dir, exist_ok=True)
        logger.info(f"Created job output directory: {job_dir}")
        
        return job_dir
    
    def get_job_output_directory(self, job_id: str) -> Optional[str]:
        """
        Find the output directory for a job
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Path to the job output directory or None if not found
        """
        # Check in all date folders
        for date_dir in os.listdir(self.output_folder):
            date_path = os.path.join(self.output_folder, date_dir)
            if os.path.isdir(date_path):
                job_dir = os.path.join(date_path, job_id)
                if os.path.isdir(job_dir):
                    return job_dir
        
        logger.warning(f"Job output directory not found for job_id: {job_id}")
        return None
    
    def create_zip_from_files(self, files: List[Dict], job_id: str) -> Optional[str]:
        """
        Create a ZIP file from a list of files
        
        Args:
            files: List of dictionaries with file information
            job_id: Job identifier for the zip file name
            
        Returns:
            Path to the created ZIP file or None if failed
        """
        try:
            # Create ZIP filename
            zip_filename = f"demucs_output_{job_id}.zip"
            zip_path = os.path.join(self.output_folder, zip_filename)
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    file_path = file_info.get('path')
                    arcname = file_info.get('name')
                    
                    if os.path.isfile(file_path):
                        zipf.write(file_path, arcname=arcname)
            
            logger.info(f"Created ZIP file: {zip_path}")
            return zip_path
        except Exception as e:
            logger.error(f"Error creating ZIP file: {str(e)}")
            return None
    
    def get_file_path(self, filename: str, folder: str = None) -> Optional[str]:
        """
        Get full path for a file
        
        Args:
            filename: Filename to look for
            folder: Folder to look in (defaults to upload folder)
            
        Returns:
            Full path to the file or None if not found
        """
        search_folder = folder if folder else self.upload_folder
        file_path = os.path.join(search_folder, filename)
        
        if os.path.isfile(file_path):
            return file_path
        
        logger.warning(f"File not found: {file_path}")
        return None
    
    def create_zip_from_directory(self, source_dir, output_path, zip_filename):
        """Create ZIP file from directory contents"""
        zip_path = os.path.join(output_path, zip_filename)
        logger.info(f"Creating ZIP file: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Check if directory exists and list contents
                logger.info(f"Files in source directory: {os.listdir(source_dir)}")
                
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # Remove base directory prefix, keep only relative path
                        arcname = os.path.relpath(src_path, source_dir)
                        logger.info(f"Adding file to ZIP: {src_path} -> {arcname}")
                        zipf.write(src_path, arcname)
            
            # Check if ZIP file was created successfully
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                logger.error(f"ZIP file creation failed or is empty: {zip_path}")
                return None
                
            logger.info(f"ZIP file created successfully: {zip_path}, size: {os.path.getsize(zip_path)} bytes")
            return zip_path
        
        except Exception as e:
            logger.error(f"Error creating ZIP file: {str(e)}")
            return None
    
    def cleanup_job_files(self, job_id: str) -> Tuple[bool, str]:
        """
        清理特定任务的文件
        
        Args:
            job_id: 任务ID
            
        Returns:
            (成功标志, 消息)
        """
        if not job_id or len(job_id) < 8:
            return False, '无效的任务ID'
        
        logger.info(f"清理任务文件: {job_id}")
        cleanup_success = False
        
        try:
            # 清理上传的原始文件
            upload_file = None
            for filename in os.listdir(self.upload_folder):
                if job_id in filename:
                    upload_file = os.path.join(self.upload_folder, filename)
                    if os.path.isfile(upload_file):
                        logger.info(f"删除上传文件: {upload_file}")
                        os.remove(upload_file)
                        cleanup_success = True
            
            # 清理输出目录中的任务文件夹
            job_output_dir = self.get_job_output_directory(job_id)
            if job_output_dir and os.path.isdir(job_output_dir):
                logger.info(f"删除任务输出目录: {job_output_dir}")
                shutil.rmtree(job_output_dir, ignore_errors=True)
                cleanup_success = True
            
            # 清理ZIP文件
            zip_file = os.path.join(self.output_folder, f"demucs_output_{job_id}.zip")
            if os.path.isfile(zip_file):
                logger.info(f"删除ZIP文件: {zip_file}")
                os.remove(zip_file)
                cleanup_success = True
            
            # 清理separated目录中可能存在的文件
            separated_dir = os.path.join(os.getcwd(), 'separated')
            if os.path.exists(separated_dir):
                for model_name in os.listdir(separated_dir):
                    model_path = os.path.join(separated_dir, model_name)
                    if os.path.isdir(model_path):
                        for item in os.listdir(model_path):
                            if job_id in item:
                                item_path = os.path.join(model_path, item)
                                if os.path.isdir(item_path):
                                    logger.info(f"删除separated目录: {item_path}")
                                    shutil.rmtree(item_path, ignore_errors=True)
                                    cleanup_success = True
            
            if cleanup_success:
                return True, "任务文件清理成功"
            else:
                return False, "未找到相关任务文件"
        
        except Exception as e:
            logger.error(f"清理文件出错: {str(e)}")
            return False, f"清理文件出错: {str(e)}"
    
    def cleanup_all_files(self) -> Tuple[bool, str, Dict]:
        """
        清理所有上传和输出文件
        
        Returns:
            (成功标志, 消息, 清理统计)
        """
        logger.info("开始清理所有文件")
        stats = {
            "uploads_deleted": 0,
            "outputs_deleted": 0,
            "separated_deleted": 0,
            "zip_files_deleted": 0
        }
        
        try:
            # 清理上传目录
            if os.path.exists(self.upload_folder):
                for filename in os.listdir(self.upload_folder):
                    file_path = os.path.join(self.upload_folder, filename)
                    if os.path.isfile(file_path):
                        logger.info(f"删除上传文件: {file_path}")
                        os.remove(file_path)
                        stats["uploads_deleted"] += 1
            
            # 清理输出目录
            if os.path.exists(self.output_folder):
                # 清理ZIP文件
                for filename in os.listdir(self.output_folder):
                    file_path = os.path.join(self.output_folder, filename)
                    if os.path.isfile(file_path) and filename.endswith('.zip'):
                        logger.info(f"删除ZIP文件: {file_path}")
                        os.remove(file_path)
                        stats["zip_files_deleted"] += 1
                
                # 清理日期子目录
                for date_dir in os.listdir(self.output_folder):
                    date_path = os.path.join(self.output_folder, date_dir)
                    if os.path.isdir(date_path):
                        for job_dir in os.listdir(date_path):
                            job_path = os.path.join(date_path, job_dir)
                            if os.path.isdir(job_path):
                                logger.info(f"删除输出目录: {job_path}")
                                shutil.rmtree(job_path, ignore_errors=True)
                                stats["outputs_deleted"] += 1
            
            # 清理separated目录
            separated_dir = os.path.join(os.getcwd(), 'separated')
            if os.path.exists(separated_dir):
                for model_name in os.listdir(separated_dir):
                    model_path = os.path.join(separated_dir, model_name)
                    if os.path.isdir(model_path):
                        for item in os.listdir(model_path):
                            item_path = os.path.join(model_path, item)
                            if os.path.isdir(item_path):
                                logger.info(f"删除separated目录: {item_path}")
                                shutil.rmtree(item_path, ignore_errors=True)
                                stats["separated_deleted"] += 1
            
            logger.info(f"文件清理完成，统计: {stats}")
            return True, "所有文件清理成功", stats
        
        except Exception as e:
            logger.error(f"清理所有文件出错: {str(e)}")
            return False, f"清理所有文件出错: {str(e)}", stats 