import os
import threading
import logging
from flask import Blueprint, request, current_app

from app.utils.helpers import (
    validate_request, 
    allowed_file, 
    generate_job_id,
    create_success_response, 
    create_error_response, 
    create_file_response
)
from app.utils.sse import SSEManager, create_sse_response

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize SSE manager
sse_manager = SSEManager()

@api_bp.route('/models', methods=['GET'])
def list_models():
    """Get list of available demucs models"""
    try:
        # 避免立即初始化AudioSeparator，返回静态的模型列表以提高响应速度
        # 可用的模型列表基于demucs库的标准模型
        available_models = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_q"]
        return create_success_response({
            'models': available_models,
            'default': current_app.config['DEFAULT_MODEL']
        })
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        return create_error_response(f"Failed to get models: {str(e)}")

@api_bp.route('/formats', methods=['GET'])
def list_output_formats():
    """Get list of supported output formats"""
    try:
        # 直接从配置获取格式，避免触发AudioSeparator初始化
        formats = current_app.config['SUPPORTED_OUTPUT_FORMATS']
        return create_success_response({
            'formats': formats,
            'default': current_app.config['DEFAULT_OUTPUT_FORMAT']
        })
    except Exception as e:
        logger.error(f"Error fetching formats: {str(e)}")
        return create_error_response(f"Failed to get formats: {str(e)}")

@api_bp.route('/qualities', methods=['GET'])
def list_quality_options():
    """Get list of available audio quality options"""
    try:
        # 直接从配置获取质量选项，避免触发AudioSeparator初始化
        quality_settings = current_app.config['AUDIO_QUALITY_SETTINGS']
        qualities = {k: v['description'] for k, v in quality_settings.items()}
        return create_success_response({
            'qualities': qualities,
            'default': current_app.config['DEFAULT_AUDIO_QUALITY']
        })
    except Exception as e:
        logger.error(f"Error fetching qualities: {str(e)}")
        return create_error_response(f"Failed to get qualities: {str(e)}")

@api_bp.route('/process', methods=['POST'])
def process_audio():
    """
    Start audio separation process
    Returns a job ID that can be used to track progress and download results
    """
    # Validate request - check for either 'file' or 'audio' field
    has_file = 'file' in request.files
    has_audio = 'audio' in request.files
    
    if not has_file and not has_audio:
        return create_error_response("No file provided")
    
    # Get uploaded file from either 'file' or 'audio' field
    file = request.files.get('file') or request.files.get('audio')
    
    # Check if file type is allowed
    if not file or not allowed_file(file.filename):
        return create_error_response("Invalid file format. Supported formats: mp3, wav, flac, ogg, m4a, mp4")
    
    try:
        # Get parameters
        model_name = request.form.get('model', current_app.config['DEFAULT_MODEL'])
        stems_param = request.form.get('stems', None)
        output_format = request.form.get('output_format', current_app.config['DEFAULT_OUTPUT_FORMAT'])
        audio_quality = request.form.get('audio_quality', current_app.config['DEFAULT_AUDIO_QUALITY'])
        
        # Validate format and quality
        if output_format not in current_app.config['SUPPORTED_OUTPUT_FORMATS']:
            return create_error_response(f"不支持的输出格式: {output_format}。支持的格式: {current_app.config['SUPPORTED_OUTPUT_FORMATS']}")
        
        if audio_quality not in current_app.config['AUDIO_QUALITY_SETTINGS']:
            return create_error_response(f"不支持的音频质量: {audio_quality}。支持的质量: {list(current_app.config['AUDIO_QUALITY_SETTINGS'].keys())}")
        
        # Parse stems if provided
        stems = None
        if stems_param:
            stems = [s.strip() for s in stems_param.split(',')]
        
        # Generate job ID
        job_id = generate_job_id()
        
        # Create job output directory
        job_output_dir = current_app.file_manager.create_job_output_directory(job_id)
        
        # Save uploaded file
        filename, file_path = current_app.file_manager.save_uploaded_file(file)
        
        logger.info(f"Starting audio separation process for job: {job_id}, format: {output_format}, quality: {audio_quality}")
        
        # Register task in SSE manager
        sse_manager.create_task(job_id)
        
        # 创建应用上下文副本以在线程中使用
        app = current_app._get_current_object()
        
        # Define progress callback for SSE
        def progress_callback(progress, message="处理中", status="processing"):
            # 更新传统SSE进度
            sse_manager.update_progress(job_id, progress=progress, message=message, status=status)
        
        # Start processing thread
        def process_thread():
            try:
                # Start demucs process with new format and quality parameters
                result = app.audio_separator.separate_track(
                    input_file=file_path,
                    output_dir=job_output_dir,
                    model_name=model_name,
                    stems=stems,
                    output_format=output_format,
                    audio_quality=audio_quality,
                    progress_callback=progress_callback
                )
                
                if result and result.get('files'):
                    # Extract file paths from result
                    output_paths = [file_info['path'] for file_info in result['files']]
                    
                    # Create a zip file from the output
                    zip_path = app.file_manager.create_zip_from_output(job_id, output_paths)
                    
                    # 设置结果文件路径 - 这是关键的修复
                    progress_callback(100, f"音频分离完成，格式: {output_format.upper()}，质量: {audio_quality}", "completed")
                    sse_manager.update_progress(job_id, progress=100, 
                                             message=f"音频分离完成，格式: {output_format.upper()}，质量: {audio_quality}", 
                                             status="completed", result_file=zip_path)
                    
                    logger.info(f"Audio separation completed for job: {job_id}, format: {output_format}, quality: {audio_quality}")
                else:
                    # If no output paths were returned, the separation failed
                    progress_callback(0, "处理失败", "error")
                    logger.error(f"Audio separation failed for job: {job_id}")
            
            except Exception as e:
                logger.error(f"Error in audio separation thread: {str(e)}")
                progress_callback(0, f"错误: {str(e)}", "error")
        
        # Start processing in a separate thread
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
        
        # Construct API URLs
        base_url = current_app.config.get('BASE_URL', '')
        status_url = f"/api/status/{job_id}"
        progress_url = f"/api/progress/{job_id}"
        download_url = f"/api/download/{job_id}"
        
        return create_success_response({
            'job_id': job_id,
            'message': 'Audio separation started',
            'status_url': status_url,
            'progress_url': progress_url,
            'download_url': download_url
        })
    
    except Exception as e:
        logger.error(f"Error starting separation process: {str(e)}")
        return create_error_response(f"Failed to start separation process: {str(e)}")

@api_bp.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get current status of a processing job"""
    progress = sse_manager.get_progress(job_id)
    
    if not progress:
        return create_error_response("Job not found", status_code=404)
    
    return create_success_response(progress)

@api_bp.route('/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    """Get progress updates using Server-Sent Events (SSE)"""
    def generate():
        # 直接返回生成器，而不是函数
        yield from sse_manager.stream_progress(job_id)
    
    return create_sse_response(generate())

@api_bp.route('/download/<job_id>', methods=['GET'])
def download_result(job_id):
    """Download the result of a completed audio separation job"""
    try:
        # Check job status
        progress = sse_manager.get_progress(job_id)
        
        if not progress:
            return create_error_response("Job not found", status_code=404)
        
        if progress['status'] != 'completed':
            return create_error_response(
                f"Job is not completed yet. Current status: {progress['status']}", 
                status_code=400
            )
        
        # Get result file path
        result_file = sse_manager.get_result_file(job_id)
        
        if not result_file or not os.path.isfile(result_file):
            return create_error_response("Result file not found", status_code=404)
        
        # Return file
        return create_file_response(result_file)
        
    except Exception as e:
        logger.error(f"Error downloading result: {str(e)}")
        return create_error_response(f"Failed to download result: {str(e)}")

@api_bp.route('/cleanup/<job_id>', methods=['DELETE'])
def cleanup_files(job_id):
    """清理特定任务的文件"""
    try:
        # 检查任务是否存在
        progress = sse_manager.get_progress(job_id)
        
        if progress:
            # 从SSE管理器中移除任务
            sse_manager.clean_task(job_id)
        
        # 清理任务相关的文件
        success, message = current_app.file_manager.cleanup_job_files(job_id)
        
        if success:
            return create_success_response({
                'message': message
            })
        else:
            return create_error_response(message, status_code=400)
        
    except Exception as e:
        logger.error(f"清理文件失败: {str(e)}")
        return create_error_response(f"清理文件失败: {str(e)}")

@api_bp.route('/admin/cleanup', methods=['POST'])
def admin_cleanup():
    """清理所有文件（需要管理员令牌）"""
    try:
        # 验证管理员令牌
        admin_token = request.headers.get('X-Admin-Token')
        
        if not admin_token or admin_token != current_app.config['ADMIN_TOKEN']:
            return create_error_response("无效的管理员令牌", status_code=403)
        
        # 清理所有SSE任务
        task_count = len(sse_manager.tasks)
        sse_manager.tasks.clear()
        
        # 清理所有文件
        success, message, stats = current_app.file_manager.cleanup_all_files()
        
        if success:
            return create_success_response({
                'message': message,
                'tasks_cleared': task_count,
                'stats': stats
            })
        else:
            return create_error_response(message, status_code=500)
        
    except Exception as e:
        logger.error(f"清理所有文件失败: {str(e)}")
        return create_error_response(f"清理所有文件失败: {str(e)}")

def init_app(app):
    app.register_blueprint(api_bp)
    logger.info("API routes initialized") 