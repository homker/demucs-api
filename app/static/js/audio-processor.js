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
        console.log('AudioProcessor initialized');
    },
    
    // 设置表单处理器
    setupFormHandlers: function() {
        // 音频处理表单
        const audioForm = document.getElementById('audioForm');
        if (audioForm) {
            audioForm.addEventListener('submit', (e) => {
                e.preventDefault();
                console.log('表单提交，开始处理音频');
                this.processAudio();
            });
            console.log('✅ 音频表单事件绑定成功');
        } else {
            console.warn('⚠️ 未找到audioForm元素');
        }
        
        // 文件选择处理
        const fileInput = document.getElementById('audioFile');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                console.log('文件选择变化:', e.target.files);
                this.handleFileChange(e.target.files[0]);
            });
            console.log('✅ 文件输入事件绑定成功');
        } else {
            console.warn('⚠️ 未找到audioFile元素');
        }
        
        // 停止按钮
        const stopBtn = document.getElementById('stopBtn');
        if (stopBtn) {
            stopBtn.addEventListener('click', () => {
                console.log('用户点击停止按钮');
                this.stopProcessing();
            });
            console.log('✅ 停止按钮事件绑定成功');
        } else {
            console.warn('⚠️ 未找到stopBtn元素');
        }
        
        // 检查进度条元素
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressContainer && progressFill && progressText) {
            console.log('✅ 进度条元素检查通过');
        } else {
            console.error('❌ 进度条元素缺失:', {
                progressContainer: !!progressContainer,
                progressFill: !!progressFill,
                progressText: !!progressText
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
            // 显示处理状态和初始化进度条
            this.showProcessingState(true);
            this.initializeProgress();
            
            window.showMessage('正在启动音频分离任务...', 'info');
            
            // 发送请求
            const response = await window.DemucsAPI.upload(
                `${window.DemucsApp.API_BASE}/api/process`,
                formData
            );
            
            console.log('API响应:', response);
            
            // 检查响应格式 - 后端将数据包装在data字段中
            if (response && response.status === 'success' && response.data && response.data.job_id) {
                this.currentJob = response.data.job_id;
                window.showMessage('处理已开始，正在监控进度...', 'success');
                
                // 监控进度
                this.monitorProgress(response.data.job_id);
            } else if (response && response.status === 'error') {
                throw new Error(response.message || '服务器返回错误');
            } else {
                // 调试信息：显示实际响应结构
                console.error('意外的响应格式:', response);
                throw new Error(`未收到有效的任务ID。响应格式: ${JSON.stringify(response)}`);
            }
            
        } catch (error) {
            console.error('处理音频失败:', error);
            window.showMessage(`处理失败: ${error.message}`, 'error');
            this.showProcessingState(false);
            this.resetProgress();
        }
    },
    
    // 初始化进度条
    initializeProgress: function() {
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressContainer) {
            progressContainer.style.display = 'block';
        }
        
        if (progressFill) {
            progressFill.style.width = '0%';
        }
        
        if (progressText) {
            progressText.textContent = '准备启动...';
        }
        
        // 初始进度更新
        window.updateProgress(0, '正在连接服务器...');
    },
    
    // 重置进度条
    resetProgress: function() {
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressContainer) {
            progressContainer.style.display = 'none';
        }
        
        if (progressFill) {
            progressFill.style.width = '0%';
        }
        
        if (progressText) {
            progressText.textContent = '0%';
        }
    },
    
    // 监控处理进度
    monitorProgress: function(jobId) {
        const streamUrl = `${window.DemucsApp.API_BASE}/api/progress/${jobId}`;
        
        console.log('开始监控进度:', streamUrl);
        
        // 设置超时检查 - 增加到60秒
        const connectionTimeout = setTimeout(() => {
            console.warn('SSE连接超时');
            window.showMessage('连接超时，但任务可能仍在后台运行', 'warning');
        }, 60000); // 从10000改为60000
        
        window.DemucsSSE.connect(streamUrl, {
            onConnect: () => {
                console.log('SSE连接已建立，开始接收进度数据');
                clearTimeout(connectionTimeout);
            },
            
            onProgress: (data) => {
                clearTimeout(connectionTimeout);
                console.log('收到进度数据:', data);
                
                if (typeof data.progress === 'number') {
                    // 确保进度条可见
                    this.showProcessingState(true);
                    window.updateProgress(data.progress, data.message || `处理中 ${data.progress}%`, 'progressFill', true);
                    this.updateJobInfo(data);
                } else {
                    console.warn('无效的进度数据:', data);
                }
            },
            
            onCompleted: (data) => {
                clearTimeout(connectionTimeout);
                console.log('处理完成:', data);
                
                // 先显示完成消息
                window.showMessage('音频处理完成！', 'success');
                window.updateProgress(100, '处理完成');
                
                // 确保showResults有足够时间执行
                setTimeout(() => {
                    console.log('延时调用showResults确保UI正确显示');
                    this.showResults(data);
                }, 100); // 延时100ms确保其他UI更新完成
                
                // 延时隐藏处理状态
                setTimeout(() => {
                    this.showProcessingState(false);
                }, 500); // 延时500ms隐藏处理状态
            },
            
            onError: (error) => {
                clearTimeout(connectionTimeout);
                console.error('SSE错误:', error);
                const errorMsg = error.message || error.error || '处理过程中出现错误';
                window.showMessage(`处理错误: ${errorMsg}`, 'error');
                this.showProcessingState(false);
                this.resetProgress();
            },
            
            onEnd: () => {
                clearTimeout(connectionTimeout);
                console.log('SSE连接结束');
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
            
            // 如果是开始处理，初始化进度条
            if (processing) {
                window.updateProgress(0, '准备启动...', 'progressFill', true);
            }
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
        if (!results) {
            console.error('未找到results元素');
            return;
        }
        
        console.log('showResults 接收到的数据:', data);
        
        let html = '<div class="card"><div class="card-body"><h4>处理结果</h4>';
        
        // 首先隐藏进度条，显示完成状态
        this.showProcessingState(false);
        
        // 处理不同的数据格式
        let outputFiles = [];
        let hasResultFile = false;
        
        if (data.output_files && data.output_files.length > 0) {
            outputFiles = data.output_files;
            hasResultFile = true;
        } else if (data.result_file) {
            // 如果有 result_file 字段，创建输出文件数组
            outputFiles = [data.result_file];
            hasResultFile = true;
        } else if (data.job_id && (data.status === 'completed' || data.progress === 100)) {
            // 如果只有 job_id 但状态是完成，尝试从API获取完整状态
            console.log('任务已完成但缺少文件信息，尝试从API获取');
            this.fetchAndShowResults(data.job_id);
            return;
        }
        
        // 优先处理完成状态
        if (data.status === 'completed' || data.progress === 100) {
            html += '<h5>下载结果:</h5>';
            html += `<p class="alert alert-success">✅ 音频分离完成！</p>`;
            
            if (hasResultFile && outputFiles.length > 0) {
                // 有具体文件信息
                outputFiles.forEach(file => {
                    const filename = file.split('/').pop();
                    // 使用job_id作为下载标识
                    const downloadUrl = data.job_id ? `/api/download/${data.job_id}` : `/api/download/${filename}`;
                    html += `<div class="mb-3">`;
                    html += `<a href="${downloadUrl}" class="btn btn-success btn-lg" download>`;
                    html += `<i class="fas fa-download"></i> 下载分离结果 (${filename})`;
                    html += `</a>`;
                    html += `</div>`;
                });
            } else if (data.job_id) {
                // 没有具体文件信息，但有job_id，生成通用下载链接
                const downloadUrl = `/api/download/${data.job_id}`;
                html += `<div class="mb-3">`;
                html += `<a href="${downloadUrl}" class="btn btn-success btn-lg" download>`;
                html += `<i class="fas fa-download"></i> 下载分离结果`;
                html += `</a>`;
                html += `</div>`;
                
                // 添加说明文字
                html += `<p class="text-muted">点击上方按钮下载已分离的音频文件（ZIP格式）</p>`;
            } else {
                html += `<p class="alert alert-warning">⚠️ 处理完成，但无法生成下载链接</p>`;
            }
        } else if (data.status === 'error') {
            html += `<p class="alert alert-danger">❌ 处理失败: ${data.message || '未知错误'}</p>`;
        } else {
            html += '<p class="alert alert-warning">⚠️ 处理中或等待结果...</p>';
        }
        
        if (data.message) {
            html += '<h5>处理信息:</h5>';
            html += `<p><strong>状态:</strong> ${data.message}</p>`;
        }
        
        if (data.job_id) {
            html += `<p><strong>任务ID:</strong> ${data.job_id}</p>`;
        }
        
        // 显示完整的数据用于调试（只在debug模式下显示）
        if (window.location.search.includes('debug=1')) {
            html += '<details><summary>完整数据 (调试用)</summary>';
            html += `<pre>${JSON.stringify(data, null, 2)}</pre>`;
            html += '</details>';
        }
        
        html += '</div></div>';
        results.innerHTML = html;
        results.style.display = 'block';
        
        // 滚动到结果区域
        if (window.DemucsUtils && window.DemucsUtils.scrollToElement) {
            window.DemucsUtils.scrollToElement(results, 20);
        } else {
            // 备用滚动方法
            results.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        
        // 显示成功消息
        if (data.status === 'completed' || data.progress === 100) {
            window.showMessage('🎉 音频分离完成！点击下载按钮获取结果。', 'success', 8000);
        }
        
        console.log('showResults 执行完成，结果已显示');
    },
    
    // 从API获取完整状态并显示结果
    fetchAndShowResults: async function(jobId) {
        try {
            console.log('从API获取任务状态:', jobId);
            const response = await fetch(`${window.DemucsApp.API_BASE}/api/status/${jobId}`);
            const statusData = await response.json();
            
            if (statusData.status === 'success' && statusData.data) {
                console.log('获取到完整状态数据:', statusData.data);
                this.showResults(statusData.data);
            } else {
                console.error('获取状态失败:', statusData);
                window.showMessage('获取处理结果失败', 'error');
            }
        } catch (error) {
            console.error('获取状态出错:', error);
            window.showMessage('获取处理结果出错', 'error');
        }
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