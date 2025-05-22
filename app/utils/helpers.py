import uuid
import logging
from flask import request, jsonify, send_file

logger = logging.getLogger(__name__)

def generate_job_id():
    """生成唯一任务ID"""
    return str(uuid.uuid4())

def validate_request(required_fields=None, file_field='file'):
    """
    验证请求数据
    
    Parameters:
    - required_fields: 必需的字段列表
    - file_field: 文件字段名
    
    Returns:
    - (bool, dict, str): (验证结果, 处理后的数据, 错误信息)
    """
    data = {}
    errors = []
    
    # 检查文件是否上传
    if file_field:
        if file_field not in request.files:
            return False, {}, '没有上传文件'
        
        file = request.files[file_field]
        if file.filename == '':
            return False, {}, '没有选择文件'
        
        data[file_field] = file
    
    # 处理表单数据
    for field in request.form:
        data[field] = request.form[field]
    
    # 检查必需字段
    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(f'缺少必需字段: {field}')
    
    if errors:
        return False, {}, '; '.join(errors)
    
    return True, data, ''

def process_boolean_param(param_value):
    """处理布尔类型参数"""
    if isinstance(param_value, bool):
        return param_value
    
    if isinstance(param_value, str):
        return param_value.lower() == 'true'
    
    return False

def create_error_response(message, status_code=400):
    """创建错误响应"""
    return jsonify({'error': message}), status_code

def create_success_response(data=None, message=None):
    """创建成功响应"""
    response = {'status': 'success'}
    
    if data:
        response.update(data)
    
    if message:
        response['message'] = message
    
    return jsonify(response)

def create_file_response(file_path, download_name=None, cleanup_id=None):
    """
    创建文件下载响应
    
    Parameters:
    - file_path: 文件路径
    - download_name: 下载文件名
    - cleanup_id: 清理ID（可选）
    
    Returns:
    - Response: 文件下载响应
    """
    try:
        if not download_name:
            download_name = file_path.split('/')[-1]
        
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
        # 添加清理ID头信息
        if cleanup_id:
            response.headers['X-Cleanup-ID'] = cleanup_id
        
        return response
    except Exception as e:
        logger.error(f"创建文件响应时出错: {str(e)}", exc_info=True)
        return create_error_response(f'处理文件时出错: {str(e)}', 500) 