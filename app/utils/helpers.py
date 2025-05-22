import uuid
import os
import random
import string
import logging
from flask import request, jsonify, send_file, current_app

logger = logging.getLogger(__name__)

def generate_job_id():
    """Generate unique job ID"""
    return str(uuid.uuid4())

def validate_request(request_obj, required_fields=None):
    """
    Validate request data
    
    Args:
        request_obj: Flask request object
        required_fields: List of required fields
    
    Returns:
        bool: True if valid, False otherwise
    """
    if required_fields:
        for field in required_fields:
            if field == 'file':
                if 'file' not in request_obj.files:
                    return False
            elif field not in request_obj.form:
                return False
    
    return True

def process_boolean_param(param_value):
    """Process boolean parameters"""
    if isinstance(param_value, bool):
        return param_value
    
    if isinstance(param_value, str):
        return param_value.lower() == 'true'
    
    return False

def create_error_response(message, status_code=400):
    """Create error response"""
    return jsonify({
        'status': 'error',
        'message': message
    }), status_code

def create_success_response(data=None, message=None):
    """Create success response"""
    response = {'status': 'success'}
    
    if data:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response)

def create_file_response(file_path, download_name=None, cleanup_id=None):
    """
    Create file download response
    
    Parameters:
    - file_path: File path
    - download_name: Download file name
    - cleanup_id: Cleanup ID (optional)
    
    Returns:
    - Response: File download response
    """
    try:
        # 确保文件路径正确，修复路径问题
        # 如果文件不存在，检查相对路径
        if not os.path.isfile(file_path):
            # 尝试查找相对于项目根目录的路径
            base_dir = current_app.config.get('BASE_DIR', os.getcwd())
            alt_path = os.path.join(base_dir, file_path)
            
            # 如果还找不到，尝试查找相对于当前工作目录的路径
            if not os.path.isfile(alt_path):
                alt_path = os.path.join(os.getcwd(), file_path)
            
            # 如果找到了替代路径，使用它
            if os.path.isfile(alt_path):
                logger.info(f"使用替代文件路径: {alt_path} 替代 {file_path}")
                file_path = alt_path
            else:
                # 记录可能的路径
                logger.error(f"无法找到文件: 原始路径={file_path}, 替代路径1={os.path.join(base_dir, file_path)}, 替代路径2={os.path.join(os.getcwd(), file_path)}")
                # 检查输出目录中的文件
                output_dir = current_app.config.get('OUTPUT_FOLDER', 'outputs')
                output_path = os.path.join(os.getcwd(), output_dir)
                logger.info(f"检查输出目录: {output_path}, 文件列表: {os.listdir(output_path) if os.path.exists(output_path) else '目录不存在'}")
                raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not download_name:
            download_name = os.path.basename(file_path)
        
        logger.info(f"发送文件: {file_path}, 下载名称: {download_name}")
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
        # Add cleanup ID header
        if cleanup_id:
            response.headers['X-Cleanup-ID'] = cleanup_id
        
        return response
    except Exception as e:
        logger.error(f"Error creating file response: {str(e)}")
        return create_error_response(f'Error processing file: {str(e)}', 500)

def allowed_file(filename):
    """
    Check if the file extension is allowed
    
    Args:
        filename: Name of the file
        
    Returns:
        bool: True if file extension is allowed
    """
    if not filename:
        return False
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def random_string(length=8):
    """
    Generate a random string of specified length
    
    Args:
        length: Length of the string to generate
        
    Returns:
        str: Random string
    """
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def make_response(data, status=200):
    """
    Create a JSON response with appropriate headers
    
    Args:
        data: Response data
        status: HTTP status code
        
    Returns:
        Response: Flask response object
    """
    response = jsonify(data)
    response.status_code = status
    return response

def validate_models(model_names):
    """
    Validate model names against available models
    
    Args:
        model_names: List of model names to validate
        
    Returns:
        tuple: (valid, error_message)
    """
    if not model_names:
        return True, None
        
    try:
        available_models = current_app.audio_separator.get_available_models()
        
        for model in model_names:
            if model != 'all' and model not in available_models:
                return False, f"Model '{model}' not found. Available models: {available_models}"
                
        return True, None
    except Exception as e:
        logger.error(f"Error validating models: {str(e)}")
        return False, f"Error validating models: {str(e)}" 