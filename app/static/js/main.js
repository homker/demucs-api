/**
 * Demucs 音频分离工具 - 主JavaScript文件
 * 包含所有页面的通用功能和工具函数
 */

// 全局配置
window.DemucsApp = {
    API_BASE: window.location.origin,
    currentStream: null,
    currentEventSource: null,
    requestId: 1,
    
    // 初始化应用
    init: function() {
        this.setupGlobalEventListeners();
        this.setupFormValidation();
        this.setupTooltips();
        console.log('Demucs App initialized');
    },
    
    // 设置全局事件监听器
    setupGlobalEventListeners: function() {
        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
        
        // 拖拽上传支持
        this.setupDragAndDrop();
    },
    
    // 设置拖拽上传
    setupDragAndDrop: function() {
        const uploadAreas = document.querySelectorAll('.upload-area');
        
        uploadAreas.forEach(area => {
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    this.handleFileSelect(files[0]);
                }
            });
            
            area.addEventListener('click', () => {
                const fileInput = area.querySelector('input[type="file"]') || 
                                 document.querySelector('input[type="file"]');
                if (fileInput) {
                    fileInput.click();
                }
            });
        });
    },
    
    // 处理文件选择
    handleFileSelect: function(file) {
        if (!file) return;
        
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            // 创建新的文件列表
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // 触发change事件
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        
        this.showMessage(`已选择文件: ${file.name}`, 'info');
    },
    
    // 表单验证
    setupFormValidation: function() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    },
    
    // 验证表单
    validateForm: function(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, '此字段为必填项');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        return isValid;
    },
    
    // 显示字段错误
    showFieldError: function(field, message) {
        this.clearFieldError(field);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-danger';
        errorDiv.textContent = message;
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        
        field.parentNode.appendChild(errorDiv);
        field.style.borderColor = 'var(--danger-color)';
    },
    
    // 清除字段错误
    clearFieldError: function(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        field.style.borderColor = '';
    },
    
    // 工具提示
    setupTooltips: function() {
        const elements = document.querySelectorAll('[data-tooltip]');
        
        elements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.getAttribute('data-tooltip'));
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    },
    
    // 显示工具提示
    showTooltip: function(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 14px;
            z-index: 1000;
            pointer-events: none;
            white-space: nowrap;
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.bottom + 5 + 'px';
        
        this.currentTooltip = tooltip;
    },
    
    // 隐藏工具提示
    hideTooltip: function() {
        if (this.currentTooltip) {
            this.currentTooltip.remove();
            this.currentTooltip = null;
        }
    }
};

// 工具函数
window.DemucsUtils = {
    // 显示消息
    showMessage: function(message, type = 'info', duration = 5000) {
        const messageContainer = this.getOrCreateMessageContainer();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type} fade-in`;
        messageDiv.textContent = message;
        
        // 添加关闭按钮
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            float: right;
            background: none;
            border: none;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            margin-left: 10px;
        `;
        closeBtn.onclick = () => messageDiv.remove();
        
        messageDiv.appendChild(closeBtn);
        messageContainer.appendChild(messageDiv);
        
        // 自动移除
        if (duration > 0) {
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, duration);
        }
        
        return messageDiv;
    },
    
    // 获取或创建消息容器
    getOrCreateMessageContainer: function() {
        let container = document.getElementById('message-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'message-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1050;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    },
    
    // 更新进度条
    updateProgress: function(progress, message = '', elementId = 'progressFill', forceShow = false) {
        const progressFill = document.getElementById(elementId);
        const progressText = document.getElementById('progressText');
        const progressContainer = document.getElementById('progressContainer');
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = message || `${progress}%`;
        }
        
        if (progressContainer) {
            // 修复逻辑：如果forceShow为true，或者进度 >= 0且已经在处理状态中，则显示进度条
            if (forceShow || (progress >= 0 && (progressContainer.style.display === 'block' || progress > 0))) {
                progressContainer.style.display = 'block';
            }
            
            if (progress >= 100) {
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                }, 3000);
            }
        }
    },
    
    // 显示加载状态
    showLoading: function(element, text = '加载中...') {
        element.classList.add('loading');
        element.setAttribute('data-original-text', element.textContent);
        element.textContent = text;
        element.disabled = true;
    },
    
    // 隐藏加载状态
    hideLoading: function(element) {
        element.classList.remove('loading');
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.textContent = originalText;
            element.removeAttribute('data-original-text');
        }
        element.disabled = false;
    },
    
    // 格式化文件大小
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 格式化时间
    formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },
    
    // 复制到剪贴板
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                this.showMessage('已复制到剪贴板', 'success', 2000);
            });
        } else {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showMessage('已复制到剪贴板', 'success', 2000);
        }
    },
    
    // 下载文件
    downloadFile: function(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    // 动画滚动到元素
    scrollToElement: function(element, offset = 0) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    },
    
    // 防抖函数
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 节流函数
    throttle: function(func, limit) {
        let lastFunc;
        let lastRan;
        return function(...args) {
            if (!lastRan) {
                func(...args);
                lastRan = Date.now();
            } else {
                clearTimeout(lastFunc);
                lastFunc = setTimeout(() => {
                    if ((Date.now() - lastRan) >= limit) {
                        func(...args);
                        lastRan = Date.now();
                    }
                }, limit - (Date.now() - lastRan));
            }
        };
    }
};

// API工具函数
window.DemucsAPI = {
    // 发送请求
    request: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    },
    
    // GET请求
    get: function(url) {
        return this.request(url, { method: 'GET' });
    },
    
    // POST请求
    post: function(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    
    // 上传文件
    upload: function(url, formData) {
        return this.request(url, {
            method: 'POST',
            body: formData,
            headers: {} // 让浏览器设置Content-Type
        });
    },
    
    // JSON-RPC请求
    jsonRpcRequest: async function(method, params = {}) {
        const request = {
            jsonrpc: "2.0",
            id: window.DemucsApp.requestId++,
            method: method,
            params: params
        };
        
        try {
            const response = await this.post(`${window.DemucsApp.API_BASE}/mcp`, request);
            
            if (response.error) {
                throw new Error(response.error.message);
            }
            
            return response.result;
        } catch (error) {
            console.error('JSON-RPC请求失败:', error);
            throw error;
        }
    },
    
    // 健康检查
    checkHealth: function() {
        return this.get(`${window.DemucsApp.API_BASE}/health`);
    },
    
    // 获取模型列表
    getModels: function() {
        return this.get(`${window.DemucsApp.API_BASE}/api/models`);
    },
    
    // 获取支持格式
    getFormats: function() {
        return this.get(`${window.DemucsApp.API_BASE}/api/formats`);
    },
    
    // 获取音质选项
    getQualities: function() {
        return this.get(`${window.DemucsApp.API_BASE}/api/qualities`);
    }
};

// SSE流处理
window.DemucsSSE = {
    currentEventSource: null,
    
    // 连接SSE流
    connect: function(url, callbacks = {}) {
        this.disconnect(); // 断开现有连接
        
        console.log('连接SSE流:', url);
        
        try {
            const eventSource = new EventSource(url);
            this.currentEventSource = eventSource;
            window.DemucsApp.currentEventSource = eventSource;
            
            // 连接成功
            eventSource.onopen = (event) => {
                console.log('SSE连接已建立');
                if (callbacks.onConnect) {
                    callbacks.onConnect();
                }
            };
            
            // 接收消息
            eventSource.onmessage = (event) => {
                try {
                    console.log('收到SSE原始数据:', event.data);
                    const data = JSON.parse(event.data);
                    this.handleMessage(data, callbacks);
                } catch (error) {
                    console.error('解析SSE数据失败:', error, '原始数据:', event.data);
                    if (callbacks.onError) {
                        callbacks.onError({
                            message: '数据解析失败',
                            error: error,
                            rawData: event.data
                        });
                    }
                }
            };
            
            // 连接错误
            eventSource.onerror = (error) => {
                console.error('SSE连接错误:', error);
                console.log('EventSource readyState:', eventSource.readyState);
                
                // 检查连接状态
                if (eventSource.readyState === EventSource.CLOSED) {
                    console.log('SSE连接已关闭');
                } else if (eventSource.readyState === EventSource.CONNECTING) {
                    console.log('SSE正在重连...');
                    return; // 浏览器会自动重连，不触发错误回调
                }
                
                if (callbacks.onError) {
                    callbacks.onError({
                        message: 'SSE连接中断',
                        error: error,
                        readyState: eventSource.readyState
                    });
                }
                
                // 自动断开连接
                setTimeout(() => {
                    this.disconnect();
                }, 1000);
            };
            
            return eventSource;
            
        } catch (error) {
            console.error('创建SSE连接失败:', error);
            if (callbacks.onError) {
                callbacks.onError({
                    message: '无法创建SSE连接',
                    error: error
                });
            }
            return null;
        }
    },
    
    // 处理消息
    handleMessage: function(data, callbacks) {
        console.log('处理SSE消息:', data);
        
        // 验证数据格式
        if (!data || typeof data !== 'object') {
            console.warn('收到无效的SSE数据格式:', data);
            return;
        }

        // 添加完成状态标记
        if (!this.taskCompleted) {
            this.taskCompleted = false;
        }

        // 判断消息类型：如果没有type字段，根据数据内容推断类型
        let messageType = data.type;
        
        if (!messageType) {
            // 根据数据内容推断消息类型
            if (typeof data.progress === 'number') {
                if (data.status === 'completed' || data.progress >= 100) {
                    messageType = 'completed';
                } else if (data.status === 'error') {
                    messageType = 'error';
                } else {
                    messageType = 'progress';
                }
            } else if (data.status === 'error') {
                messageType = 'error';
            } else if (data.status === 'completed') {
                messageType = 'completed';
            } else if (data.message === 'Stream closed') {
                // 如果任务已完成，忽略Stream closed消息，避免干扰UI
                if (this.taskCompleted) {
                    console.log('任务已完成，忽略Stream closed消息');
                    return;
                }
                messageType = 'end';
            } else {
                messageType = 'info'; // 默认为信息消息
            }
        }
        
        switch (messageType) {
            case 'progress':
                if (callbacks.onProgress) {
                    callbacks.onProgress(data);
                }
                // 验证进度数据
                if (typeof data.progress === 'number' && data.progress >= 0 && data.progress <= 100) {
                    window.DemucsUtils.updateProgress(data.progress, data.message || `${data.progress}%`, 'progressFill', true);
                } else {
                    console.warn('无效的进度数据:', data.progress);
                }
                break;
                
            case 'completed':
                console.log('任务完成:', data);
                this.taskCompleted = true; // 标记任务已完成
                
                if (callbacks.onCompleted) {
                    callbacks.onCompleted(data);
                }
                window.DemucsUtils.updateProgress(100, data.message || '处理完成');
                
                // 延长断开连接的时间，确保UI有足够时间更新
                setTimeout(() => {
                    console.log('延时断开SSE连接...');
                    this.disconnect();
                }, 3000); // 从1000ms改为3000ms，给UI更多时间
                break;
                
            case 'error':
                console.error('收到错误消息:', data);
                if (callbacks.onError) {
                    callbacks.onError(data);
                }
                window.DemucsUtils.showMessage(data.message || '处理出现错误', 'error');
                this.disconnect();
                break;
                
            case 'info':
                if (data.message) {
                    console.log('收到信息消息:', data.message);
                }
                break;
                
            case 'warning':
                if (data.message) {
                    window.DemucsUtils.showMessage(data.message, 'warning');
                }
                break;
                
            case 'end':
                console.log('收到结束信号');
                // 如果任务已完成，不要立即断开连接，让UI有时间显示结果
                if (this.taskCompleted) {
                    console.log('任务已完成，延迟断开连接');
                    setTimeout(() => this.disconnect(), 2000);
                } else {
                    console.log('任务未完成，立即断开连接');
                    if (callbacks.onEnd) {
                        callbacks.onEnd(data);
                    }
                    this.disconnect();
                }
                break;
                
            default:
                console.log('收到其他类型消息:', messageType, data);
                if (callbacks.onMessage) {
                    callbacks.onMessage(data);
                }
        }
    },
    
    // 断开连接
    disconnect: function() {
        if (this.currentEventSource) {
            console.log('断开SSE连接');
            this.currentEventSource.close();
            this.currentEventSource = null;
        }
        
        if (window.DemucsApp.currentEventSource) {
            window.DemucsApp.currentEventSource.close();
            window.DemucsApp.currentEventSource = null;
        }
        
        // 重置完成状态标记
        this.taskCompleted = false;
    },
    
    // 检查连接状态
    isConnected: function() {
        return this.currentEventSource && this.currentEventSource.readyState === EventSource.OPEN;
    },
    
    // 获取连接状态描述
    getConnectionStatus: function() {
        if (!this.currentEventSource) {
            return 'disconnected';
        }
        
        switch (this.currentEventSource.readyState) {
            case EventSource.CONNECTING:
                return 'connecting';
            case EventSource.OPEN:
                return 'connected';
            case EventSource.CLOSED:
                return 'closed';
            default:
                return 'unknown';
        }
    }
};

// 清理函数
window.DemucsApp.cleanup = function() {
    // 断开SSE连接
    window.DemucsSSE.disconnect();
    
    // 清理定时器
    if (this.intervals) {
        this.intervals.forEach(interval => clearInterval(interval));
    }
    
    // 清理工具提示
    window.DemucsUtils.hideTooltip();
    
    console.log('应用清理完成');
};

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.DemucsApp.init();
});

// 导出到全局
window.showMessage = window.DemucsUtils.showMessage.bind(window.DemucsUtils);
window.updateProgress = window.DemucsUtils.updateProgress.bind(window.DemucsUtils);
window.showLoading = window.DemucsUtils.showLoading.bind(window.DemucsUtils);
window.hideLoading = window.DemucsUtils.hideLoading.bind(window.DemucsUtils); 