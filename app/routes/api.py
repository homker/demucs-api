import os
import uuid
import logging
from flask import Blueprint, request, send_file, jsonify, current_app
from werkzeug.utils import secure_filename

from app.utils import (
    allowed_file, 
    generate_job_id, 
    validate_request, 
    process_boolean_param, 
    create_error_response, 
    create_success_response, 
    create_file_response, 
    SSEManager, 
    create_sse_response
)

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize SSE manager
sse_manager = SSEManager()

@api_bp.route('/models', methods=['GET'])
def list_models():
    """Get list of available Demucs models"""
    try:
        audio_separator = current_app.audio_separator
        available_models = audio_separator.get_available_models()
        
        return create_success_response({
            'models': available_models
        })
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        return create_error_response(f"Failed to get available models: {str(e)}")

@api_bp.route('/process', methods=['POST'])
def process_audio():
    """
    Start audio separation process
    Returns a job ID that can be used to track progress and download results
    """
    # Validate request
    if not validate_request(request, ['file']):
        return create_error_response("No file provided")
    
    # Get uploaded file
    file = request.files['file']
    
    # Check if file type is allowed
    if not file or not allowed_file(file.filename):
        return create_error_response("Invalid file format. Supported formats: mp3, wav, flac, ogg, m4a, mp4")
    
    try:
        # Get parameters
        model_name = request.form.get('model', current_app.config.DEFAULT_MODEL)
        stems_param = request.form.get('stems', None)
        
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
        
        logger.info(f"Starting audio separation process for job: {job_id}")
        
        # Register task in SSE manager
        sse_manager.create_task(job_id)
        
        # Start audio separation in a background thread
        def process_task():
            try:
                # Define progress callback
                def update_progress(job_id, progress, message, status=None, result_file=None):
                    sse_manager.update_progress(job_id, progress, message, status, result_file)
                
                # Run audio separation
                result = current_app.audio_separator.separate_track(
                    input_file=file_path,
                    output_dir=job_output_dir,
                    model_name=model_name,
                    stems=stems,
                    progress_callback=lambda p, m, s=None, r=None: update_progress(job_id, p, m, s, r)
                )
                
                # Create ZIP of output files
                zip_path = current_app.file_manager.create_zip_from_files(result['files'], job_id)
                
                # Update task with completion and result file
                sse_manager.update_progress(
                    job_id, 
                    100, 
                    "Processing completed", 
                    "completed",
                    zip_path
                )
                
                logger.info(f"Audio separation completed for job: {job_id}")
                
            except Exception as e:
                logger.error(f"Error processing audio: {str(e)}")
                sse_manager.set_error(job_id, f"Error: {str(e)}")
        
        # Run in background
        import threading
        thread = threading.Thread(target=process_task)
        thread.daemon = True
        thread.start()
        
        # Return job ID for status tracking
        return create_success_response({
            'job_id': job_id,
            'message': 'Audio separation started',
            'status_url': f"/api/status/{job_id}",
            'progress_url': f"/api/progress/{job_id}",
            'download_url': f"/api/download/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error starting audio separation: {str(e)}")
        return create_error_response(f"Failed to start audio separation: {str(e)}")

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
        return sse_manager.stream_progress(job_id)
    
    return create_sse_response(generate)

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