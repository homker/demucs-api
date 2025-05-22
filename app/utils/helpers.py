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
        if not download_name:
            download_name = os.path.basename(file_path)
        
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
           filename.rsplit('.', 1)[1].lower() in current_app.config.ALLOWED_EXTENSIONS

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