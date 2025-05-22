import os
import logging
from flask import Blueprint, request, current_app, after_this_request

from app.utils.helpers import (
    validate_request, process_boolean_param, create_error_response,
    create_success_response, create_file_response, generate_job_id
)

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return create_success_response(message="服务正常运行")

@api_bp.route('/separate', methods=['POST'])
def separate_audio():
    """
    音频分离API接口
    - 上传一个音频文件
    - 返回分离后的音频文件（压缩包格式）
    """
    # 验证请求
    valid, data, error = validate_request()
    if not valid:
        return create_error_response(error)
    
    # 获取文件和参数
    file = data['file']
    model_name = data.get('model', current_app.config['DEFAULT_MODEL'])
    two_stems = data.get('two_stems', None)
    
    # 分段长度，根据模型类型设置默认值
    segment = data.get('segment', None)
    
    # 处理布尔参数
    mp3 = process_boolean_param(data.get('mp3', 'false'))
    mp3_bitrate = data.get('mp3_bitrate', str(current_app.config['DEFAULT_MP3_BITRATE']))
    
    try:
        # 生成唯一ID作为处理任务标识
        job_id = generate_job_id()
        
        # 获取服务实例
        file_manager = current_app.file_manager
        audio_separator = current_app.audio_separator
        
        # 创建输出目录
        output_path = file_manager.get_output_path(job_id)
        os.makedirs(output_path, exist_ok=True)
        
        # 保存上传的文件
        file_path = file_manager.save_uploaded_file(file, job_id)
        
        # 调用音频分离服务
        success, model_name, model_output_dir = audio_separator.separate_audio(
            file_path=file_path,
            model_name=model_name,
            two_stems=two_stems,
            segment=segment,
            mp3=mp3,
            mp3_bitrate=mp3_bitrate,
            output_path=output_path
        )
        
        if not success or not model_output_dir:
            return create_error_response('音频分离失败', 500)
        
        # 查找音轨输出目录
        track_output_dir = audio_separator.find_track_output_dir(model_output_dir, file.filename)
        
        if not track_output_dir:
            return create_error_response('处理完成但找不到对应音轨输出文件夹', 500)
        
        # 创建ZIP文件
        filename_without_ext = os.path.splitext(file.filename)[0]
        zip_filename = f"{filename_without_ext}_separated.zip"
        zip_path = file_manager.create_zip_from_directory(track_output_dir, output_path, zip_filename)
        
        if not zip_path:
            return create_error_response('ZIP文件创建失败', 500)
        
        # 在请求结束后清理上传的原始文件（但保留ZIP文件供下载）
        @after_this_request
        def cleanup_after_download(response):
            try:
                # 清理上传目录中的原始音频文件
                upload_path = file_manager.get_upload_path(job_id)
                if os.path.exists(upload_path):
                    logger.info(f"清理上传目录: {upload_path}")
                    file_manager._cleanup_directory(upload_path, float('inf'))  # 立即清理
                
                # 清理分离后的文件夹（但保留ZIP文件）
                separated_dir = os.path.join(os.getcwd(), 'separated')
                if os.path.exists(separated_dir):
                    model_dir = os.path.join(separated_dir, model_name)
                    if os.path.exists(model_dir):
                        for item in os.listdir(model_dir):
                            item_path = os.path.join(model_dir, item)
                            if filename_without_ext.lower() in item.lower() and os.path.isdir(item_path):
                                logger.info(f"删除分离后的音轨目录: {item_path}")
                                file_manager._cleanup_directory(item_path, float('inf'))  # 立即清理
                
            except Exception as e:
                logger.error(f"清理文件时出错: {str(e)}", exc_info=True)
            
            return response
        
        # 创建文件下载响应
        return create_file_response(zip_path, zip_filename, job_id)
        
    except Exception as e:
        logger.error(f"处理错误: {str(e)}", exc_info=True)
        return create_error_response(f'处理错误: {str(e)}', 500)

@api_bp.route('/cleanup/<cleanup_id>', methods=['DELETE'])
def cleanup_files(cleanup_id):
    """
    清理特定任务的临时文件
    - cleanup_id: 任务ID，与X-Cleanup-ID头信息对应
    """
    try:
        file_manager = current_app.file_manager
        success, message = file_manager.cleanup_files(cleanup_id)
        
        if success:
            return create_success_response(message=message)
        else:
            return create_error_response(message, 400)
            
    except Exception as e:
        logger.error(f"清理文件出错: {str(e)}", exc_info=True)
        return create_error_response(f"清理文件出错: {str(e)}", 500) 