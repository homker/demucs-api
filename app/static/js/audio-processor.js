/**
 * 音频处理相关功能
 * 包含音频分离、MCP测试、实时进度监控等
 */

window.AudioProcessor = {
    // 当前任务
    currentJob: null,
    
    // 初始化
    init: function() {
        this.setupFormHandlers();
        this.setupMCPHandlers();
        console.log('AudioProcessor initialized');
    },
    
    // 设置表单处理器
    setupFormHandlers: function() {
        // 音频处理表单
        const audioForm = document.getElementById('audioForm');
        if (audioForm) {
            audioForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.processAudio();
            });
        }
        
        // 文件选择处理
        const fileInput = document.getElementById('audioFile');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileChange(e.target.files[0]);
            });
        }
        
        // 停止按钮
        const stopBtn = document.getElementById('stopBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                this.stopProcessing();
            });
        }
    },
    
    // 处理文件选择
    handleFileChange: function(file) {
        if (!file) return;
        
        // 验证文件类型
        const validTypes = ['audio/mp3', 'audio/wav', 'audio/m4a', 'audio/flac', 'audio/ogg'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|flac|ogg)$/i)) {
            window.showMessage('请选择有效的音频文件格式', 'error');
            return;
        }
        
        // 验证文件大小 (100MB)
        if (file.size > 100 * 1024 * 1024) {
            window.showMessage('文件大小不能超过100MB', 'error');
            return;
        }
        
        // 显示文件信息
        const fileInfo = document.getElementById('fileInfo');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div class="alert alert-info">
                    <strong>已选择文件:</strong> ${file.name}<br>
                    <strong>大小:</strong> ${window.DemucsUtils.formatFileSize(file.size)}<br>
                    <strong>类型:</strong> ${file.type || '未知'}
                </div>
            `;
        }
        
        window.showMessage(`已选择文件: ${file.name}`, 'success');
    },
    
    // 处理音频
    processAudio: async function() {
        const formData = new FormData();
        const fileInput = document.getElementById('audioFile');
        const modelSelect = document.getElementById('model');
        const stemsSelect = document.getElementById('stems');
        const formatSelect = document.getElementById('outputFormat');
        const qualitySelect = document.getElementById('audioQuality');
        
        // 验证文件
        if (!fileInput || !fileInput.files[0]) {
            window.showMessage('请选择音频文件', 'error');
            return;
        }
        
        // 构建表单数据
        formData.append('audio', fileInput.files[0]);
        if (modelSelect) formData.append('model', modelSelect.value);
        if (stemsSelect) formData.append('stems', stemsSelect.value);
        if (formatSelect) formData.append('output_format', formatSelect.value);
        if (qualitySelect) formData.append('audio_quality', qualitySelect.value);
        
        try {
            // 显示处理状态
            this.showProcessingState(true);
            
            // 发送请求
            const response = await window.DemucsAPI.upload(
                `${window.DemucsApp.API_BASE}/api/process`,
                formData
            );
            
            if (response.job_id) {
                this.currentJob = response.job_id;
                window.showMessage('处理已开始，正在监控进度...', 'info');
                
                // 监控进度
                this.monitorProgress(response.job_id);
            } else {
                throw new Error('未收到任务ID');
            }
            
        } catch (error) {
            window.showMessage(`处理失败: ${error.message}`, 'error');
            this.showProcessingState(false);
        }
    },
    
    // 监控处理进度
    monitorProgress: function(jobId) {
        const streamUrl = `${window.DemucsApp.API_BASE}/api/stream/${jobId}`;
        
        window.DemucsSSE.connect(streamUrl, {
            onProgress: (data) => {
                window.updateProgress(data.progress, data.message);
                this.updateJobInfo(data);
            },
            
            onCompleted: (data) => {
                window.showMessage('音频处理完成！', 'success');
                this.showResults(data);
                this.showProcessingState(false);
            },
            
            onError: (error) => {
                window.showMessage(`处理错误: ${error.message || '未知错误'}`, 'error');
                this.showProcessingState(false);
            },
            
            onEnd: () => {
                this.showProcessingState(false);
            }
        });
    },
    
    // 停止处理
    stopProcessing: function() {
        if (this.currentJob) {
            // 发送停止请求
            fetch(`${window.DemucsApp.API_BASE}/api/stop/${this.currentJob}`, {
                method: 'POST'
            }).then(() => {
                window.showMessage('处理已停止', 'warning');
            });
        }
        
        // 断开SSE连接
        window.DemucsSSE.disconnect();
        this.showProcessingState(false);
        this.currentJob = null;
    },
    
    // 显示处理状态
    showProcessingState: function(processing) {
        const processBtn = document.getElementById('processBtn');
        const stopBtn = document.getElementById('stopBtn');
        const progressContainer = document.getElementById('progressContainer');
        
        if (processBtn) {
            if (processing) {
                window.showLoading(processBtn, '处理中...');
            } else {
                window.hideLoading(processBtn);
            }
        }
        
        if (stopBtn) {
            stopBtn.style.display = processing ? 'inline-block' : 'none';
        }
        
        if (progressContainer) {
            progressContainer.style.display = processing ? 'block' : 'none';
        }
    },
    
    // 更新任务信息
    updateJobInfo: function(data) {
        const jobInfo = document.getElementById('jobInfo');
        if (jobInfo) {
            jobInfo.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h4>处理进度</h4>
                        <p><strong>任务ID:</strong> ${this.currentJob}</p>
                        <p><strong>进度:</strong> ${data.progress}%</p>
                        <p><strong>状态:</strong> ${data.message}</p>
                        <p><strong>开始时间:</strong> ${new Date().toLocaleString()}</p>
                    </div>
                </div>
            `;
        }
    },
    
    // 显示结果
    showResults: function(data) {
        const results = document.getElementById('results');
        if (!results) return;
        
        let html = '<div class="card"><div class="card-body"><h4>处理结果</h4>';
        
        if (data.output_files && data.output_files.length > 0) {
            html += '<h5>输出文件:</h5><ul>';
            data.output_files.forEach(file => {
                const filename = file.split('/').pop();
                html += `<li><a href="${file}" download="${filename}" class="btn btn-success btn-sm">下载 ${filename}</a></li>`;
            });
            html += '</ul>';
        }
        
        if (data.metadata) {
            html += '<h5>处理信息:</h5>';
            html += `<pre>${JSON.stringify(data.metadata, null, 2)}</pre>`;
        }
        
        html += '</div></div>';
        results.innerHTML = html;
        results.style.display = 'block';
        
        // 滚动到结果区域
        window.DemucsUtils.scrollToElement(results, 20);
    }
};

// MCP测试功能
window.MCPTester = {
    // 初始化
    init: function() {
        this.setupMCPHandlers();
        console.log('MCPTester initialized');
    },
    
    // 设置MCP处理器
    setupMCPHandlers: function() {
        // 绑定所有MCP测试按钮
        this.bindButton('checkHealth', this.checkHealth);
        this.bindButton('getCapabilities', this.getCapabilities);
        this.bindButton('listTools', this.listTools);
        this.bindButton('listResources', this.listResources);
        this.bindButton('getModels', this.getModels);
        this.bindButton('startAudioSeparation', this.startAudioSeparation);
        this.bindButton('stopStream', this.stopStream);
        this.bindButton('clearLogs', this.clearLogs);
    },
    
    // 绑定按钮
    bindButton: function(id, handler) {
        const button = document.querySelector(`button[onclick="${id}()"]`);
        if (button) {
            button.removeAttribute('onclick');
            button.addEventListener('click', handler.bind(this));
        }
    },
    
    // 日志记录
    log: function(message, type = 'info') {
        const logOutput = document.getElementById('logOutput');
        if (!logOutput) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
        logEntry.className = `alert alert-${type}`;
        logOutput.appendChild(logEntry);
        logOutput.scrollTop = logOutput.scrollHeight;
    },
    
    // 清空日志
    clearLogs: function() {
        const logOutput = document.getElementById('logOutput');
        if (logOutput) {
            logOutput.innerHTML = '';
        }
    },
    
    // 检查健康状态
    checkHealth: async function() {
        try {
            this.log('检查服务器健康状态...', 'info');
            const data = await window.DemucsAPI.checkHealth();
            
            const output = document.getElementById('healthOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            }
            this.log('✅ 服务器健康检查成功', 'success');
        } catch (error) {
            this.log(`❌ 健康检查失败: ${error.message}`, 'error');
            const output = document.getElementById('healthOutput');
            if (output) {
                output.innerHTML = `<div class="alert alert-error">错误: ${error.message}</div>`;
            }
        }
    },
    
    // 获取服务器能力
    getCapabilities: async function() {
        try {
            this.log('初始化MCP连接...', 'info');
            const result = await window.DemucsAPI.jsonRpcRequest('initialize', {
                protocolVersion: '1.0',
                capabilities: {},
                clientInfo: {
                    name: 'mcp-test-client',
                    version: '1.0.0'
                }
            });
            
            const output = document.getElementById('healthOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            }
            this.log('✅ MCP初始化成功', 'success');
        } catch (error) {
            this.log(`❌ MCP初始化失败: ${error.message}`, 'error');
        }
    },
    
    // 列出工具
    listTools: async function() {
        try {
            this.log('获取工具列表...', 'info');
            const result = await window.DemucsAPI.jsonRpcRequest('tools/list');
            
            const output = document.getElementById('toolsOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            }
            this.log('✅ 工具列表获取成功', 'success');
        } catch (error) {
            this.log(`❌ 获取工具列表失败: ${error.message}`, 'error');
        }
    },
    
    // 列出资源
    listResources: async function() {
        try {
            this.log('获取资源列表...', 'info');
            const result = await window.DemucsAPI.jsonRpcRequest('resources/list');
            
            const output = document.getElementById('toolsOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
            }
            this.log('✅ 资源列表获取成功', 'success');
        } catch (error) {
            this.log(`❌ 获取资源列表失败: ${error.message}`, 'error');
        }
    },
    
    // 获取模型
    getModels: async function() {
        try {
            this.log('获取模型列表...', 'info');
            const result = await window.DemucsAPI.jsonRpcRequest('tools/call', {
                name: 'get_models',
                arguments: {}
            });
            
            const models = JSON.parse(result.content[0].text);
            
            const output = document.getElementById('toolsOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(models, null, 2)}</pre>`;
            }
            this.log('✅ 模型列表获取成功', 'success');
        } catch (error) {
            this.log(`❌ 获取模型列表失败: ${error.message}`, 'error');
        }
    },
    
    // 开始音频分离
    startAudioSeparation: async function() {
        try {
            // 获取选择的参数
            const model = document.getElementById('modelSelect')?.value || 'htdemucs';
            const stemCheckboxes = document.querySelectorAll('input[type="checkbox"]:checked');
            const stems = Array.from(stemCheckboxes).map(cb => cb.value);
            
            if (stems.length === 0) {
                this.log('❌ 请至少选择一个音轨类型', 'error');
                return;
            }
            
            this.log(`开始音频分离 - 模型: ${model}, 音轨: ${stems.join(', ')}`, 'info');
            
            // 创建测试文件路径
            const testFilePath = '/tmp/test_audio_demo.mp3';
            
            // 调用音频分离工具
            const result = await window.DemucsAPI.jsonRpcRequest('tools/call', {
                name: 'separate_audio',
                arguments: {
                    file_path: testFilePath,
                    model: model,
                    stems: stems,
                    stream_progress: true
                }
            });
            
            const taskInfo = JSON.parse(result.content[0].text);
            
            if (taskInfo.error) {
                this.log(`❌ 任务启动失败: ${taskInfo.error}`, 'error');
                return;
            }
            
            this.log(`✅ 任务已启动 - ID: ${taskInfo.job_id}`, 'success');
            
            // 显示进度条
            const progressContainer = document.getElementById('progressContainer');
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
            
            // 开始监听SSE流
            if (taskInfo.stream_url) {
                this.startSSEStream(taskInfo.job_id);
            }
            
            // 显示任务信息
            const output = document.getElementById('separationOutput');
            if (output) {
                output.innerHTML = `<pre>${JSON.stringify(taskInfo, null, 2)}</pre>`;
            }
            
        } catch (error) {
            this.log(`❌ 音频分离失败: ${error.message}`, 'error');
        }
    },
    
    // 开始SSE流
    startSSEStream: function(jobId) {
        const streamUrl = `${window.DemucsApp.API_BASE}/mcp/stream/${jobId}`;
        this.log(`📡 连接到SSE流: ${streamUrl}`, 'info');
        
        window.DemucsSSE.connect(streamUrl, {
            onMessage: (data) => {
                if (data.type === 'progress') {
                    window.updateProgress(data.progress, data.message);
                    this.log(`📊 进度更新: ${data.progress}% - ${data.message}`, 'info');
                } else if (data.type === 'completed') {
                    window.updateProgress(100, data.message);
                    this.log(`✅ 任务完成: ${data.message}`, 'success');
                    if (data.output_files) {
                        this.log(`📁 输出文件: ${data.output_files.join(', ')}`, 'success');
                    }
                } else if (data.type === 'error') {
                    this.log(`❌ 处理错误: ${data.message}`, 'error');
                } else if (data.type === 'end') {
                    this.log('📡 流已结束', 'info');
                }
                
                // 更新输出显示
                const output = document.getElementById('separationOutput');
                if (output) {
                    output.innerHTML += `<div>${JSON.stringify(data, null, 2)}</div>\n`;
                    output.scrollTop = output.scrollHeight;
                }
            },
            
            onError: () => {
                this.log('❌ SSE连接错误', 'error');
            }
        });
    },
    
    // 停止流
    stopStream: function() {
        window.DemucsSSE.disconnect();
        this.log('📡 SSE连接已关闭', 'info');
    }
};

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 根据页面类型初始化不同功能
    if (document.getElementById('audioForm')) {
        window.AudioProcessor.init();
    }
    
    if (document.getElementById('logOutput')) {
        window.MCPTester.init();
        // 自动检查服务器状态
        setTimeout(() => {
            window.MCPTester.log('🚀 MCP测试页面已加载', 'success');
            window.MCPTester.log(`📍 API Base URL: ${window.DemucsApp.API_BASE}`, 'info');
            window.MCPTester.log('🔌 使用标准JSON-RPC 2.0协议', 'info');
            window.MCPTester.checkHealth();
        }, 500);
    }
}); 