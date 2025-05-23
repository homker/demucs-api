/**
 * MCP SSE客户端适配器
 * 提供与服务器发送事件(SSE)的连接和通信功能
 */

class MCPSSEClient {
    /**
     * 创建MCP SSE客户端
     * @param {string} baseUrl - API基础URL
     * @param {Object} options - 配置选项
     */
    constructor(baseUrl = '', options = {}) {
        this.baseUrl = baseUrl;
        this.options = Object.assign({
            reconnectInterval: 3000,      // 重连间隔(毫秒)
            maxReconnectAttempts: 5,      // 最大重连尝试次数
            heartbeatTimeout: 35000,      // 心跳超时(毫秒)
            autoReconnect: true,          // 是否自动重连
            debug: false                  // 是否启用调试日志
        }, options);
        
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.listeners = {
            message: [],
            progress: [],
            error: [],
            connected: [],
            reconnecting: [],
            closed: []
        };
        
        this.currentJobId = null;
    }
    
    /**
     * 连接到SSE进度流
     * @param {string} jobId - 任务ID
     * @returns {Promise} 连接建立的Promise
     */
    connect(jobId) {
        return new Promise((resolve, reject) => {
            if (this.eventSource) {
                this.disconnect();
            }
            
            this.currentJobId = jobId;
            const url = `${this.baseUrl}/mcp/progress/${jobId}`;
            this.debug(`正在连接到SSE: ${url}`);
            
            try {
                this.eventSource = new EventSource(url);
                
                // 设置事件监听器
                this.eventSource.onopen = () => {
                    this.debug('SSE连接已建立');
                    this.reconnectAttempts = 0;
                    this._startHeartbeatTimer();
                    this._triggerEvent('connected');
                    resolve();
                };
                
                this.eventSource.onmessage = (event) => {
                    this._resetHeartbeatTimer();
                    
                    try {
                        const data = JSON.parse(event.data);
                        this.debug('收到SSE消息:', data);
                        
                        // 触发消息事件
                        this._triggerEvent('message', data);
                        
                        // 触发进度事件
                        if ('progress' in data) {
                            this._triggerEvent('progress', data);
                        }
                        
                        // 如果任务完成或出错，关闭连接
                        if (['completed', 'error', '音频分离完成', 'cleaned'].includes(data.status)) {
                            this.debug(`任务状态为 ${data.status}，正在关闭连接`);
                            this.disconnect();
                        }
                    } catch (error) {
                        this.debug('解析SSE消息出错:', error);
                    }
                };
                
                this.eventSource.onerror = (error) => {
                    this.debug('SSE连接错误:', error);
                    this._triggerEvent('error', error);
                    
                    if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
                        this._reconnect();
                    } else {
                        this.disconnect();
                        reject(new Error('SSE连接错误'));
                    }
                };
                
            } catch (error) {
                this.debug('创建SSE连接出错:', error);
                reject(error);
            }
        });
    }
    
    /**
     * 断开SSE连接
     */
    disconnect() {
        if (this.eventSource) {
            this.debug('正在断开SSE连接');
            this.eventSource.close();
            this.eventSource = null;
            this._clearHeartbeatTimer();
            this._triggerEvent('closed');
        }
    }
    
    /**
     * 获取任务当前状态
     * @param {string} jobId - 任务ID
     * @returns {Promise} 包含任务状态的Promise
     */
    async getStatus(jobId = null) {
        const targetJobId = jobId || this.currentJobId;
        
        if (!targetJobId) {
            throw new Error('未指定任务ID');
        }
        
        const url = `${this.baseUrl}/mcp/status/${targetJobId}`;
        this.debug(`正在获取任务状态: ${url}`);
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.message);
        }
        
        return data.data;
    }
    
    /**
     * 清理任务资源
     * @param {string} jobId - 任务ID
     * @returns {Promise} 清理操作的Promise
     */
    async cleanup(jobId = null) {
        const targetJobId = jobId || this.currentJobId;
        
        if (!targetJobId) {
            throw new Error('未指定任务ID');
        }
        
        const url = `${this.baseUrl}/mcp/cleanup/${targetJobId}`;
        this.debug(`正在清理任务资源: ${url}`);
        
        const response = await fetch(url, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.status === 'error') {
            throw new Error(data.message);
        }
        
        return data.data;
    }
    
    /**
     * 添加事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     * @returns {MCPSSEClient} 当前客户端实例，支持链式调用
     */
    on(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        }
        return this;
    }
    
    /**
     * 移除事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 要移除的回调函数
     * @returns {MCPSSEClient} 当前客户端实例，支持链式调用
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
        return this;
    }
    
    /**
     * 触发事件
     * @private
     * @param {string} event - 事件名称
     * @param {*} data - 事件数据
     */
    _triggerEvent(event, data) {
        if (this.listeners[event]) {
            for (const callback of this.listeners[event]) {
                try {
                    callback(data);
                } catch (error) {
                    this.debug(`执行 ${event} 回调时出错:`, error);
                }
            }
        }
    }
    
    /**
     * 重新连接到SSE
     * @private
     */
    _reconnect() {
        this.reconnectAttempts++;
        this._triggerEvent('reconnecting', this.reconnectAttempts);
        this.debug(`正在尝试重新连接 (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);
        
        setTimeout(() => {
            if (this.currentJobId) {
                this.connect(this.currentJobId).catch(error => {
                    this.debug('重新连接失败:', error);
                });
            }
        }, this.options.reconnectInterval);
    }
    
    /**
     * 启动心跳计时器
     * @private
     */
    _startHeartbeatTimer() {
        this._clearHeartbeatTimer();
        this.heartbeatTimer = setTimeout(() => {
            this.debug('心跳超时，尝试重新连接');
            if (this.eventSource) {
                this.eventSource.close();
                this._reconnect();
            }
        }, this.options.heartbeatTimeout);
    }
    
    /**
     * 重置心跳计时器
     * @private
     */
    _resetHeartbeatTimer() {
        this._clearHeartbeatTimer();
        this._startHeartbeatTimer();
    }
    
    /**
     * 清除心跳计时器
     * @private
     */
    _clearHeartbeatTimer() {
        if (this.heartbeatTimer) {
            clearTimeout(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    /**
     * 输出调试信息
     * @private
     * @param {...*} args - 调试参数
     */
    debug(...args) {
        if (this.options.debug) {
            console.debug('[MCP-SSE]', ...args);
        }
    }
}

// 导出为全局变量
window.MCPSSEClient = MCPSSEClient; 