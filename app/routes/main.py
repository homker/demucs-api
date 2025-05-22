import logging
from flask import Blueprint, render_template, current_app

from app.utils.helpers import create_success_response

logger = logging.getLogger(__name__)

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET'])
def index():
    """首页"""
    # 这里我们使用render_template渲染模板
    # 但由于原代码直接返回HTML字符串，我们暂时保持原样
    # 后续可以将HTML移到templates目录下的模板文件中
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
                    <pre>POST /api/separate
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
                    <pre>GET /api/health</pre>
                    <p>用于检查服务是否正常运行。</p>
                </div>
                
                <div class="card">
                    <h3>3. 文件清理 API</h3>
                    <pre>DELETE /api/cleanup/{cleanup_id}</pre>
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
                    
                    <pre>curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "mp3=true" http://localhost:5000/api/separate -o separated.zip</pre>
                    
                    <h4>two_stems 参数示例</h4>
                    <pre>curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "two_stems=vocals" -F "mp3=true" http://localhost:5000/api/separate -o vocals_separate.zip</pre>
                    
                    <h4>清理文件示例</h4>
                    <pre>
# 1. 分离音频并获取清理ID
curl -X POST -F "file=@song.mp3" -F "model=htdemucs" -F "mp3=true" \
    -D headers.txt http://localhost:5000/api/separate -o separated.zip

# 2. 从响应头获取清理ID
CLEANUP_ID=$(grep -i "X-Cleanup-ID" headers.txt | cut -d' ' -f2 | tr -d '\r')

# 3. 调用清理API
curl -X DELETE http://localhost:5000/api/cleanup/$CLEANUP_ID</pre>
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

@main_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口（保留旧的路径，新路径在api路由中）"""
    return create_success_response(message="服务正常运行") 