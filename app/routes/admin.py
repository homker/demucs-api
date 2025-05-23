#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理面板路由
Admin panel routes with authentication
"""

import os
import time
import shutil
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app, send_file
from functools import wraps
from pathlib import Path

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证账号密码
        if (username == current_app.config['ADMIN_USERNAME'] and 
            password == current_app.config['ADMIN_PASSWORD']):
            session['admin_authenticated'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin_login.html', error='用户名或密码错误')
    
    # 如果已经登录，直接跳转到管理面板
    if session.get('admin_authenticated'):
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """退出登录"""
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_required
def dashboard():
    """管理面板主页"""
    base_url = current_app.config.get('BASE_URL', '')
    return render_template('admin.html', base_url=base_url)

@admin_bp.route('/api/files')
@admin_required
def get_files():
    """获取文件列表API - 按任务分组"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        file_retention_minutes = current_app.config['FILE_RETENTION_MINUTES']
        
        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        current_time = time.time()
        tasks = {}  # 按任务ID分组
        orphaned_files = []  # 无法识别任务的文件
        total_size = 0
        old_files_count = 0
        
        # 扫描上传文件夹
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    modified_time = stat.st_mtime
                    size = stat.st_size
                    total_size += size
                    
                    # 判断是否过期
                    is_old = (current_time - modified_time) > (file_retention_minutes * 60)
                    if is_old:
                        old_files_count += 1
                    
                    file_info = {
                        'name': file,
                        'path': file_path,
                        'size': size,
                        'modified_time': modified_time,
                        'is_old': is_old,
                        'type': 'input'
                    }
                    
                    # 尝试从文件名提取任务ID (格式: name_taskid.ext)
                    if '_' in file and '.' in file:
                        # 获取文件名部分（不含扩展名）
                        name_part = os.path.splitext(file)[0]
                        if '_' in name_part:
                            # 取最后一个下划线后的部分作为任务ID
                            task_id = name_part.split('_')[-1]
                            if len(task_id) >= 6:  # 任务ID通常比较长
                                if task_id not in tasks:
                                    tasks[task_id] = {
                                        'task_id': task_id,
                                        'created_time': modified_time,
                                        'input_files': [],
                                        'output_files': [],
                                        'total_size': 0,
                                        'is_old': is_old,
                                        'status': 'unknown'
                                    }
                                tasks[task_id]['input_files'].append(file_info)
                                tasks[task_id]['total_size'] += size
                                tasks[task_id]['created_time'] = min(tasks[task_id]['created_time'], modified_time)
                                continue
                    
                    # 无法识别任务ID的文件
                    orphaned_files.append(file_info)
                    
                except OSError:
                    continue
        
        # 扫描输出文件夹
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    modified_time = stat.st_mtime
                    size = stat.st_size
                    total_size += size
                    
                    # 判断是否过期
                    is_old = (current_time - modified_time) > (file_retention_minutes * 60)
                    if is_old:
                        old_files_count += 1
                    
                    file_info = {
                        'name': file,
                        'path': file_path,
                        'size': size,
                        'modified_time': modified_time,
                        'is_old': is_old,
                        'type': 'output'
                    }
                    
                    # 尝试从文件名或目录名提取任务ID
                    task_id = None
                    
                    # 方法1: 从文件名提取（格式: name_stem.ext）
                    if '_' in file and '.' in file:
                        name_part = os.path.splitext(file)[0]
                        if '_' in name_part:
                            base_name = '_'.join(name_part.split('_')[:-1])  # 去掉最后的stem部分
                            # 检查是否与现有任务匹配
                            for tid in tasks:
                                for input_file in tasks[tid]['input_files']:
                                    input_base = os.path.splitext(input_file['name'])[0]
                                    if input_base.startswith(base_name.split('_')[0]):  # 原始文件名匹配
                                        task_id = tid
                                        break
                                if task_id:
                                    break
                    
                    # 方法2: 从目录名提取
                    if not task_id:
                        dir_name = os.path.basename(root)
                        if dir_name in tasks:
                            task_id = dir_name
                        elif len(dir_name) >= 6 and dir_name != output_folder:
                            # 创建新任务
                            if dir_name not in tasks:
                                tasks[dir_name] = {
                                    'task_id': dir_name,
                                    'created_time': modified_time,
                                    'input_files': [],
                                    'output_files': [],
                                    'total_size': 0,
                                    'is_old': is_old,
                                    'status': 'completed'
                                }
                            task_id = dir_name
                    
                    if task_id and task_id in tasks:
                        tasks[task_id]['output_files'].append(file_info)
                        tasks[task_id]['total_size'] += size
                        if tasks[task_id]['output_files']:
                            tasks[task_id]['status'] = 'completed'
                    else:
                        orphaned_files.append(file_info)
                    
                except OSError:
                    continue
        
        # 计算任务统计信息
        task_list = []
        for task_id, task_info in tasks.items():
            # 确定任务状态
            if task_info['output_files']:
                task_info['status'] = 'completed'
            elif task_info['input_files']:
                task_info['status'] = 'processing'
            else:
                task_info['status'] = 'unknown'
                
            # 确定任务是否过期（基于最新文件时间）
            latest_time = task_info['created_time']
            for f in task_info['input_files'] + task_info['output_files']:
                latest_time = max(latest_time, f['modified_time'])
            
            task_info['is_old'] = (current_time - latest_time) > (file_retention_minutes * 60)
            task_info['latest_time'] = latest_time
            
            task_list.append(task_info)
        
        # 按最新时间排序（最新的在前）
        task_list.sort(key=lambda x: x['latest_time'], reverse=True)
        orphaned_files.sort(key=lambda x: x['modified_time'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'data': {
                'tasks': task_list,
                'orphaned_files': orphaned_files,
                'summary': {
                    'total_tasks': len(task_list),
                    'completed_tasks': len([t for t in task_list if t['status'] == 'completed']),
                    'processing_tasks': len([t for t in task_list if t['status'] == 'processing']),
                    'old_tasks': len([t for t in task_list if t['is_old']]),
                    'total_size': total_size,
                    'orphaned_files_count': len(orphaned_files),
                    'old_files_count': old_files_count
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取文件列表失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'获取文件列表失败: {str(e)}'
        }), 500

@admin_bp.route('/api/cleanup/old', methods=['POST'])
@admin_required
def cleanup_old_files():
    """清理过期文件API"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        file_retention_minutes = current_app.config['FILE_RETENTION_MINUTES']
        
        current_time = time.time()
        deleted_count = 0
        
        # 清理上传文件夹中的过期文件
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    modified_time = os.path.getmtime(file_path)
                    if (current_time - modified_time) > (file_retention_minutes * 60):
                        os.remove(file_path)
                        deleted_count += 1
                        current_app.logger.info(f"删除过期上传文件: {file_path}")
                except OSError as e:
                    current_app.logger.error(f"删除文件失败 {file_path}: {e}")
        
        # 清理输出文件夹中的过期文件
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    modified_time = os.path.getmtime(file_path)
                    if (current_time - modified_time) > (file_retention_minutes * 60):
                        os.remove(file_path)
                        deleted_count += 1
                        current_app.logger.info(f"删除过期输出文件: {file_path}")
                except OSError as e:
                    current_app.logger.error(f"删除文件失败 {file_path}: {e}")
        
        # 清理空目录
        for folder in [upload_folder, output_folder]:
            for root, dirs, files in os.walk(folder, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # 空目录
                            os.rmdir(dir_path)
                            current_app.logger.info(f"删除空目录: {dir_path}")
                    except OSError:
                        pass
        
        return jsonify({
            'status': 'success',
            'message': f'成功清理 {deleted_count} 个过期文件'
        })
        
    except Exception as e:
        current_app.logger.error(f"清理过期文件失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'清理过期文件失败: {str(e)}'
        }), 500

@admin_bp.route('/api/cleanup/all', methods=['POST'])
@admin_required
def cleanup_all_files():
    """清理所有文件API"""
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        deleted_count = 0
        
        # 清理上传文件夹
        if os.path.exists(upload_folder):
            for item in os.listdir(upload_folder):
                item_path = os.path.join(upload_folder, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        deleted_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_count += 1
                    current_app.logger.info(f"删除: {item_path}")
                except OSError as e:
                    current_app.logger.error(f"删除失败 {item_path}: {e}")
        
        # 清理输出文件夹
        if os.path.exists(output_folder):
            for item in os.listdir(output_folder):
                item_path = os.path.join(output_folder, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        deleted_count += 1
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        deleted_count += 1
                    current_app.logger.info(f"删除: {item_path}")
                except OSError as e:
                    current_app.logger.error(f"删除失败 {item_path}: {e}")
        
        return jsonify({
            'status': 'success',
            'message': f'成功清理 {deleted_count} 个文件/目录'
        })
        
    except Exception as e:
        current_app.logger.error(f"清理所有文件失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'清理所有文件失败: {str(e)}'
        }), 500

@admin_bp.route('/api/files/delete', methods=['POST'])
@admin_required
def delete_file():
    """删除单个文件API"""
    try:
        data = request.get_json()
        if not data or 'file_path' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少文件路径参数'
            }), 400
        
        file_path = data['file_path']
        
        # 安全检查：确保文件在允许的目录内
        upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        output_folder = os.path.abspath(current_app.config['OUTPUT_FOLDER'])
        file_path_abs = os.path.abspath(file_path)
        
        if not (file_path_abs.startswith(upload_folder) or file_path_abs.startswith(output_folder)):
            return jsonify({
                'status': 'error',
                'message': '无权删除此文件'
            }), 403
        
        if not os.path.exists(file_path):
            return jsonify({
                'status': 'error',
                'message': '文件不存在'
            }), 404
        
        # 删除文件
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
        
        current_app.logger.info(f"管理员删除文件: {file_path}")
        
        return jsonify({
            'status': 'success',
            'message': '文件删除成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"删除文件失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'删除文件失败: {str(e)}'
        }), 500

@admin_bp.route('/api/files/download')
@admin_required
def download_file():
    """下载文件API"""
    try:
        file_path = request.args.get('file_path')
        if not file_path:
            return jsonify({
                'status': 'error',
                'message': '缺少文件路径参数'
            }), 400
        
        # 安全检查：确保文件在允许的目录内
        upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        output_folder = os.path.abspath(current_app.config['OUTPUT_FOLDER'])
        file_path_abs = os.path.abspath(file_path)
        
        if not (file_path_abs.startswith(upload_folder) or file_path_abs.startswith(output_folder)):
            return jsonify({
                'status': 'error',
                'message': '无权下载此文件'
            }), 403
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({
                'status': 'error',
                'message': '文件不存在'
            }), 404
        
        # 获取文件名
        filename = os.path.basename(file_path)
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        current_app.logger.error(f"下载文件失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'下载文件失败: {str(e)}'
        }), 500

@admin_bp.route('/api/tasks/delete', methods=['POST'])
@admin_required
def delete_task():
    """删除整个任务及其相关文件API"""
    try:
        data = request.get_json()
        if not data or 'task_id' not in data:
            return jsonify({
                'status': 'error',
                'message': '缺少任务ID参数'
            }), 400
        
        task_id = data['task_id']
        upload_folder = current_app.config['UPLOAD_FOLDER']
        output_folder = current_app.config['OUTPUT_FOLDER']
        
        deleted_files = []
        deleted_count = 0
        
        # 删除上传文件夹中相关的文件
        for root, dirs, files in os.walk(upload_folder):
            for file in files:
                if task_id in file:  # 文件名包含任务ID
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        deleted_files.append(file_path)
                        deleted_count += 1
                        current_app.logger.info(f"删除任务文件: {file_path}")
                    except OSError as e:
                        current_app.logger.error(f"删除文件失败 {file_path}: {e}")
        
        # 删除输出文件夹中相关的文件和目录
        for root, dirs, files in os.walk(output_folder):
            # 检查是否是任务目录
            if task_id in os.path.basename(root):
                try:
                    shutil.rmtree(root)
                    deleted_files.append(root)
                    deleted_count += 1
                    current_app.logger.info(f"删除任务目录: {root}")
                    break  # 避免继续遍历已删除的目录
                except OSError as e:
                    current_app.logger.error(f"删除目录失败 {root}: {e}")
            else:
                # 检查文件名是否包含任务ID
                for file in files:
                    if task_id in file:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_path)
                            deleted_count += 1
                            current_app.logger.info(f"删除任务文件: {file_path}")
                        except OSError as e:
                            current_app.logger.error(f"删除文件失败 {file_path}: {e}")
        
        return jsonify({
            'status': 'success',
            'message': f'成功删除任务 {task_id} 的 {deleted_count} 个文件/目录',
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        current_app.logger.error(f"删除任务失败: {e}")
        return jsonify({
            'status': 'error',
            'message': f'删除任务失败: {str(e)}'
        }), 500 