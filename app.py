import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file, after_this_request
import torch
import shutil
import zipfile
from pathlib import Path
import logging
import time
import threading
import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 设置上传文件最大为200MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['FILE_RETENTION_MINUTES'] = 30  # 文件保留时间（分钟）

# 确保上传和输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 清理过期文件的函数
def cleanup_old_files(retention_minutes=None):
    """清理过期的临时文件和目录"""
    if retention_minutes is None:
        retention_minutes = app.config['FILE_RETENTION_MINUTES']
    
    logger.info(f"开始清理超过 {retention_minutes} 分钟的临时文件...")
    
    # 获取当前时间
    now = time.time()
    cutoff_time = now - (retention_minutes * 60)
    
    # 清理上传目录
    cleanup_directory(app.config['UPLOAD_FOLDER'], cutoff_time)
    
    # 清理输出目录
    cleanup_directory(app.config['OUTPUT_FOLDER'], cutoff_time)
    
    # 清理分离后的音频目录（如果存在）
    separated_dir = os.path.join(os.getcwd(), 'separated')
    if os.path.exists(separated_dir):
        cleanup_directory(separated_dir, cutoff_time)
    
    logger.info("清理完成")

def cleanup_directory(directory, cutoff_time):
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

# 启动定期清理任务
def start_cleanup_scheduler():
    """启动一个后台线程，定期清理过期文件"""
    def cleanup_task():
        while True:
            try:
                cleanup_old_files()
            except Exception as e:
                logger.error(f"定期清理任务出错: {str(e)}", exc_info=True)
            
            # 每小时运行一次清理
            time.sleep(3600)
    
    # 创建并启动清理线程
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("后台清理任务已启动")

# 启动清理任务
start_cleanup_scheduler()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'ok'})

@app.route('/cleanup/<cleanup_id>', methods=['DELETE'])
def cleanup_files(cleanup_id):
    """
    清理特定任务的临时文件
    - cleanup_id: 任务ID，与X-Cleanup-ID头信息对应
    """
    if not cleanup_id or len(cleanup_id) < 32:
        return jsonify({'error': '无效的清理ID'}), 400
    
    # 验证ID格式 (应该是UUID格式)
    try:
        uuid.UUID(cleanup_id)
    except ValueError:
        return jsonify({'error': '无效的清理ID格式'}), 400
    
    logger.info(f"清理任务ID: {cleanup_id} 的文件")
    
    cleanup_success = False
    cleanup_message = ""
    
    try:
        # 清理上传目录
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], cleanup_id)
        if os.path.exists(upload_path) and os.path.isdir(upload_path):
            logger.info(f"清理上传目录: {upload_path}")
            shutil.rmtree(upload_path, ignore_errors=True)
            cleanup_success = True
        
        # 清理输出目录
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], cleanup_id)
        if os.path.exists(output_path) and os.path.isdir(output_path):
            logger.info(f"清理输出目录: {output_path}")
            shutil.rmtree(output_path, ignore_errors=True)
            cleanup_success = True
        
        # 清理分离后的音频目录中对应的文件
        separated_dir = os.path.join(os.getcwd(), 'separated')
        if os.path.exists(separated_dir):
            model_dirs = [os.path.join(separated_dir, d) for d in os.listdir(separated_dir) if os.path.isdir(os.path.join(separated_dir, d))]
            
            for model_dir in model_dirs:
                # 尝试找到与任务ID相关的分离音频目录
                # 可能需要基于输出结构调整逻辑
                job_related_dirs = []
                
                # 由于分离的音频目录可能不直接包含任务ID，我们需要查看是否有任务期间创建的目录
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
            cleanup_message = "文件清理成功"
        else:
            cleanup_message = "没有找到相关文件"
        
        return jsonify({
            'status': 'success',
            'message': cleanup_message
        })
    
    except Exception as e:
        logger.error(f"清理文件时出错: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f"清理文件时出错: {str(e)}"
        }), 500

@app.route('/separate', methods=['POST'])
def separate_audio():
    """
    音频分离API接口
    - 上传一个音频文件
    - 返回分离后的音频文件（压缩包格式）
    """
    # 检查是否有文件上传
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 获取参数
    model_name = request.form.get('model', 'htdemucs')  # 默认使用htdemucs模型
    two_stems = request.form.get('two_stems', None)  # 分为两个音轨（如：vocals和accompaniment）
    
    # 分段长度，Hybrid Transformer模型最大支持7.8秒，必须使用整数
    default_segment = '7' if 'htdemucs' in model_name else '10'
    segment = request.form.get('segment', default_segment)
    
    mp3 = request.form.get('mp3', 'false').lower() == 'true'  # 是否输出MP3格式
    mp3_bitrate = request.form.get('mp3_bitrate', '320')  # MP3比特率
    
    try:
        # 生成唯一ID作为处理任务标识
        job_id = str(uuid.uuid4())
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], job_id)
        
        os.makedirs(upload_path, exist_ok=True)
        os.makedirs(output_path, exist_ok=True)
        
        # 保存上传的文件
        file_path = os.path.join(upload_path, file.filename)
        file.save(file_path)
        
        logger.info(f"已保存文件: {file_path}")
        
        # 构建Demucs命令 - 修复参数格式
        cmd_args = ['--device', 'cpu', '-n', model_name, '--segment', segment]
        
        if two_stems:
            cmd_args.append('--two-stems')
            cmd_args.append(two_stems)
        
        if mp3:
            cmd_args.append('--mp3')
            cmd_args.append('--mp3-bitrate')
            cmd_args.append(mp3_bitrate)
        
        cmd_args.append(file_path)
        
        # 设置输出路径环境变量
        os.environ["DEMUCS_OUTPUT"] = output_path
        
        logger.info(f"开始分离音频，参数: {' '.join(cmd_args)}")
        
        # 调用Demucs进行分离
        import demucs.separate
        demucs.separate.main(cmd_args)
        
        # 分离完成后，查找输出文件夹
        # Demucs 默认输出目录是 separated/{model_name}
        separated_dir = os.path.join(os.getcwd(), 'separated')
        logger.info(f"查找分离结果目录: {separated_dir}")
        
        if not os.path.exists(separated_dir):
            logger.error(f"找不到分离结果目录: {separated_dir}")
            return jsonify({'error': '处理完成但找不到分离结果目录'}), 500
            
        model_output_dir = os.path.join(separated_dir, model_name)
        logger.info(f"模型输出目录: {model_output_dir}")
        
        if not os.path.exists(model_output_dir):
            logger.error(f"找不到模型输出目录: {model_output_dir}")
            return jsonify({'error': '处理完成但找不到模型输出目录'}), 500
            
        # 尝试找到音频文件对应的目录
        filename_without_ext = os.path.splitext(file.filename)[0]
        logger.info(f"查找音频文件名(不含扩展名): {filename_without_ext}")
        
        # 列出所有可能的候选目录
        all_dirs = os.listdir(model_output_dir)
        logger.info(f"模型输出目录中的所有子目录: {all_dirs}")
        
        # 查找匹配的目录
        track_output_dir = None
        for dir_name in all_dirs:
            if filename_without_ext.lower() in dir_name.lower():
                track_output_dir = os.path.join(model_output_dir, dir_name)
                logger.info(f"找到匹配的音轨输出目录: {track_output_dir}")
                break
                
        # 如果找不到精确匹配，使用第一个目录（假设只处理一个文件）
        if not track_output_dir and len(all_dirs) > 0:
            track_output_dir = os.path.join(model_output_dir, all_dirs[0])
            logger.info(f"未找到精确匹配，使用第一个目录: {track_output_dir}")
            
        if not track_output_dir or not os.path.exists(track_output_dir):
            logger.error(f"找不到音轨输出目录")
            return jsonify({'error': '处理完成但找不到对应音轨输出文件夹'}), 500
        
        # 创建ZIP文件
        zip_filename = f"{filename_without_ext}_separated.zip"
        zip_path = os.path.join(output_path, zip_filename)
        logger.info(f"创建ZIP文件: {zip_path}")
        
        try:
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # 检查目录是否存在并列出内容
                logger.info(f"音轨输出目录中的文件: {os.listdir(track_output_dir)}")
                
                for root, dirs, files in os.walk(track_output_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        # 移除基础目录前缀，只保留相对路径
                        arcname = os.path.relpath(src_path, track_output_dir)
                        logger.info(f"添加文件到ZIP: {src_path} -> {arcname}")
                        zipf.write(src_path, arcname)
            
            # 检查ZIP文件是否成功创建
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
                logger.error(f"ZIP文件创建失败或为空: {zip_path}")
                return jsonify({'error': 'ZIP文件创建失败'}), 500
                
            logger.info(f"ZIP文件创建成功: {zip_path}, 大小: {os.path.getsize(zip_path)} 字节")
            
            # 在请求结束后清理上传的原始文件（但保留ZIP文件供下载）
            @after_this_request
            def cleanup_after_download(response):
                try:
                    # 清理上传目录中的原始音频文件
                    if os.path.exists(upload_path):
                        logger.info(f"清理上传目录: {upload_path}")
                        shutil.rmtree(upload_path, ignore_errors=True)
                    
                    # 清理分离后的文件夹（但保留ZIP文件）
                    separated_dir = os.path.join(os.getcwd(), 'separated')
                    if os.path.exists(separated_dir):
                        logger.info(f"清理分离目录: {separated_dir}")
                        # 这里不删除整个separated目录，而是只删除当前处理的文件对应的子目录
                        model_dir = os.path.join(separated_dir, model_name)
                        if os.path.exists(model_dir):
                            for item in os.listdir(model_dir):
                                item_path = os.path.join(model_dir, item)
                                if filename_without_ext.lower() in item.lower() and os.path.isdir(item_path):
                                    logger.info(f"删除分离后的音轨目录: {item_path}")
                                    shutil.rmtree(item_path, ignore_errors=True)
                    
                    # ZIP文件会由定期清理任务在30分钟后删除
                    
                except Exception as e:
                    logger.error(f"清理文件时出错: {str(e)}", exc_info=True)
                
                return response
            
            # 构造响应对象，添加job_id头信息
            response = send_file(
                zip_path,
                as_attachment=True,
                download_name=zip_filename,
                mimetype='application/zip'
            )
            
            # 添加清理ID头信息
            response.headers['X-Cleanup-ID'] = job_id
            
            return response
        except Exception as e:
            logger.error(f"创建或发送ZIP文件时出错: {str(e)}", exc_info=True)
            return jsonify({'error': f'处理ZIP文件时出错: {str(e)}'}), 500
    
    except Exception as e:
        logger.error(f"处理错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'处理错误: {str(e)}'}), 500
    
    finally:
        # 清理逻辑已移至after_this_request装饰器和定期清理任务中
        pass

@app.route('/', methods=['GET'])
def index():
    """API使用说明页面"""
    return """
    <html>
        <head>
            <title>Demucs API 服务</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                :root {
                    --primary-color: #3498db;
                    --secondary-color: #2c3e50;
                    --bg-color: #f9f9f9;
                    --text-color: #333;
                    --code-bg: #f0f4f8;
                    --border-radius: 8px;
                    --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 0;
                    padding: 0; 
                    line-height: 1.6;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                }
                
                header {
                    background-color: var(--primary-color);
                    color: white;
                    padding: 2rem 0;
                    text-align: center;
                    margin-bottom: 2rem;
                }
                
                h1 { 
                    margin: 0;
                    font-size: 2.5rem;
                }
                
                h2 { 
                    color: var(--secondary-color);
                    border-bottom: 2px solid var(--primary-color);
                    padding-bottom: 0.5rem;
                    margin-top: 2rem;
                }
                
                h3 {
                    color: var(--secondary-color);
                }
                
                code { 
                    background-color: var(--code-bg); 
                    padding: 2px 5px; 
                    border-radius: 3px;
                    font-family: 'Courier New', Courier, monospace;
                    font-size: 0.9em;
                }
                
                pre { 
                    background-color: var(--code-bg);
                    padding: 15px; 
                    border-radius: var(--border-radius);
                    overflow-x: auto;
                    border-left: 4px solid var(--primary-color);
                }
                
                .container { 
                    max-width: 900px; 
                    margin: 0 auto;
                    padding: 0 20px 40px;
                }
                
                .card {
                    background: white;
                    border-radius: var(--border-radius);
                    box-shadow: var(--box-shadow);
                    padding: 20px;
                    margin-bottom: 20px;
                }
                
                .model-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }
                
                .model-card {
                    background: white;
                    border-radius: var(--border-radius);
                    box-shadow: var(--box-shadow);
                    padding: 20px;
                    border-top: 4px solid var(--primary-color);
                }
                
                .model-name {
                    font-weight: bold;
                    font-size: 1.2em;
                    color: var(--primary-color);
                    margin-bottom: 10px;
                }
                
                .badge {
                    display: inline-block;
                    font-size: 0.8em;
                    background: #e8f4fd;
                    color: var(--primary-color);
                    padding: 3px 8px;
                    border-radius: 12px;
                    margin-right: 5px;
                }
                
                .parameter-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                
                .parameter-table th,
                .parameter-table td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }
                
                .parameter-table th {
                    background-color: var(--code-bg);
                    font-weight: bold;
                }
                
                .example-section {
                    margin-top: 30px;
                }
                
                .example-tabs {
                    display: flex;
                    margin-bottom: 15px;
                }
                
                .example-tab {
                    padding: 8px 16px;
                    background: #e0e0e0;
                    cursor: pointer;
                    border-radius: 4px 4px 0 0;
                    margin-right: 5px;
                }
                
                .example-tab.active {
                    background: var(--code-bg);
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <header>
                <div class="container">
                    <h1>Demucs 音轨分离 API</h1>
                    <p>基于深度学习的高质量音频源分离服务</p>
                </div>
            </header>
            
            <div class="container">
                <div class="card">
                    <h2>API 功能简介</h2>
                    <p>Demucs 是由 Facebook AI Research 开发的先进音频源分离模型，能够将混合音频分离为不同的音轨组件。本 API 服务提供了便捷的接口，可通过 HTTP 请求进行音频分离处理。</p>
                </div>
                
                <h2>API 使用方法</h2>
                
                <div class="card">
                    <h3>1. 音频分离 API</h3>
                    <pre>POST /separate
Content-Type: multipart/form-data</pre>
                    
                    <h4>请求参数</h4>
                    <table class="parameter-table">
                        <tr>
                            <th>参数名</th>
                            <th>类型</th>
                            <th>必选</th>
                            <th>说明</th>
                        </tr>
                        <tr>
                            <td><code>file</code></td>
                            <td>文件</td>
                            <td>是</td>
                            <td>要上传的音频文件 (支持 mp3, wav, flac 等格式)</td>
                        </tr>
                        <tr>
                            <td><code>model</code></td>
                            <td>字符串</td>
                            <td>否</td>
                            <td>使用的模型名称 (默认: htdemucs) 具体说明参考下文 支持模型部分</td>
                        </tr>
                        <tr>
                            <td><code>two_stems</code></td>
                            <td>字符串</td>
                            <td>否</td>
                            <td>仅分离为两个音轨，可选值: vocals, drums, bass, other, 具体说明参考下文two_stems 分离模式部分</td>
                        </tr>
                        <tr>
                            <td><code>segment</code></td>
                            <td>整数</td>
                            <td>否</td>
                            <td>分段长度 (htdemucs模型默认7秒，其他模型默认10秒)</td>
                        </tr>
                        <tr>
                            <td><code>mp3</code></td>
                            <td>布尔值</td>
                            <td>否</td>
                            <td>是否输出MP3格式 (默认: false，输出WAV格式)</td>
                        </tr>
                        <tr>
                            <td><code>mp3_bitrate</code></td>
                            <td>整数</td>
                            <td>否</td>
                            <td>MP3比特率 (默认: 320)</td>
                        </tr>
                    </table>
                    
                    <h4>响应</h4>
                    <p>成功时返回一个ZIP文件，包含分离后的各个音轨。</p>
                    <p>响应头中包含 <code>X-Cleanup-ID</code> 字段，可用于后续调用清理API。</p>
                    
                    <h5>响应头</h5>
                    <table class="parameter-table">
                        <tr>
                            <th>头名称</th>
                            <th>说明</th>
                        </tr>
                        <tr>
                            <td><code>X-Cleanup-ID</code></td>
                            <td>任务ID，可用于调用清理API删除临时文件</td>
                        </tr>
                    </table>
                </div>
                
                <div class="card">
                    <h3>2. 健康检查 API</h3>
                    <pre>GET /health</pre>
                    <p>用于检查服务是否正常运行。</p>
                </div>
                
                <div class="card">
                    <h3>3. 文件清理 API</h3>
                    <pre>DELETE /cleanup/{cleanup_id}</pre>
                    <p>清理特定任务产生的临时文件。</p>
                    
                    <h4>请求参数</h4>
                    <table class="parameter-table">
                        <tr>
                            <th>参数名</th>
                            <th>类型</th>
                            <th>位置</th>
                            <th>说明</th>
                        </tr>
                        <tr>
                            <td><code>cleanup_id</code></td>
                            <td>字符串</td>
                            <td>URL路径</td>
                            <td>要清理的任务ID，来自分离API响应的X-Cleanup-ID头</td>
                        </tr>
                    </table>
                    
                    <h4>响应</h4>
                    <pre>{
  "status": "success",
  "message": "文件清理成功"
}</pre>
                </div>
                
                <h2>示例</h2>
                <div class="card example-section">
                    <div class="example-tabs">
                        <div class="example-tab active">Curl</div>
                    </div>
                    
                    <pre>curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "mp3=true" http://localhost:5000/separate -o separated.zip</pre>
                    
                    <h4>two_stems 参数示例</h4>
                    <pre>curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "two_stems=vocals" -F "mp3=true" http://localhost:5000/separate -o vocals_separate.zip</pre>
                    
                    <h4>清理文件示例</h4>
                    <pre>
# 1. 分离音频并获取清理ID
curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "mp3=true" \
    -D headers.txt http://localhost:5000/separate -o separated.zip

# 2. 从响应头获取清理ID
CLEANUP_ID=$(grep -i "X-Cleanup-ID" headers.txt | cut -d' ' -f2 | tr -d '\r')

# 3. 调用清理API
curl -X DELETE http://localhost:5000/cleanup/$CLEANUP_ID</pre>
                </div>
                
                <h2>支持的模型</h2>
                <div class="model-grid">
                    <div class="model-card">
                        <div class="model-name">htdemucs <span class="badge">默认</span></div>
                        <p><strong>特点:</strong> Hybrid Transformer Demucs，最新的混合架构模型</p>
                        <p><strong>适用场景:</strong> 高质量分离，平衡了质量和速度</p>
                        <p><strong>支持音轨:</strong> vocals（人声）, drums（鼓）, bass（贝斯）, other（其他）</p>
                    </div>
                    
                    <div class="model-card">
                        <div class="model-name">htdemucs_ft <span class="badge">高质量</span></div>
                        <p><strong>特点:</strong> htdemucs的微调版本，更准确但处理速度更慢</p>
                        <p><strong>适用场景:</strong> 需要最高质量分离，对速度要求不高</p>
                        <p><strong>支持音轨:</strong> vocals, drums, bass, other</p>
                    </div>
                    
                    <div class="model-card">
                        <div class="model-name">htdemucs_6s <span class="badge">6音轨</span></div>
                        <p><strong>特点:</strong> 6音轨版本，增加了钢琴和吉他音轨</p>
                        <p><strong>适用场景:</strong> 需要分离钢琴和吉他的场景</p>
                        <p><strong>支持音轨:</strong> vocals, drums, bass, other, piano（钢琴）, guitar（吉他）</p>
                    </div>
                    
                    <div class="model-card">
                        <div class="model-name">mdx <span class="badge">平衡</span></div>
                        <p><strong>特点:</strong> 仅在MusDB HQ上训练的模型</p>
                        <p><strong>适用场景:</strong> 一般用途，性能适中</p>
                        <p><strong>支持音轨:</strong> vocals, drums, bass, other</p>
                    </div>
                    
                    <div class="model-card">
                        <div class="model-name">mdx_q <span class="badge">快速</span></div>
                        <p><strong>特点:</strong> mdx的量化版本，体积更小，处理速度更快</p>
                        <p><strong>适用场景:</strong> 速度敏感场景，对质量要求不高</p>
                        <p><strong>支持音轨:</strong> vocals, drums, bass, other</p>
                        <p><strong>依赖:</strong> 需要安装diffq库</p>
                    </div>
                </div>
                
                <h2>two_stems 分离模式</h2>
                <div class="card">
                    <p>使用 <code>two_stems</code> 参数可以只分离一个音轨和其余音轨，处理更快且文件更少：</p>
                    <ul>
                        <li><code>two_stems=vocals</code>: 分离为人声(vocals)和伴奏(accompaniment)</li>
                        <li><code>two_stems=drums</code>: 分离为鼓点(drums)和其他乐器(no_drums)</li>
                        <li><code>two_stems=bass</code>: 分离为贝斯(bass)和其他乐器(no_bass)</li>
                        <li><code>two_stems=other</code>: 分离为其他乐器(other)和主要乐器(no_other)</li>
                    </ul>
                </div>
                
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 