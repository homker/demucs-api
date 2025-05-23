/**
 * 调试脚本 - 检查页面元素和功能
 */

window.DemucsDebug = {
    // 检查页面元素
    checkElements: function() {
        console.group('🔍 检查页面元素');
        
        const elements = [
            'audioForm',
            'audioFile', 
            'processBtn',
            'stopBtn',
            'progressContainer',
            'progressFill',
            'progressText',
            'model',
            'stems',
            'outputFormat',
            'audioQuality'
        ];
        
        const missing = [];
        const present = [];
        
        elements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                present.push(id);
                console.log(`✅ ${id}:`, element);
            } else {
                missing.push(id);
                console.error(`❌ ${id}: 未找到`);
            }
        });
        
        console.log(`总结: ${present.length}个元素正常, ${missing.length}个元素缺失`);
        
        if (missing.length > 0) {
            console.error('缺失元素:', missing);
        }
        
        console.groupEnd();
        return { present, missing };
    },
    
    // 检查JavaScript对象
    checkObjects: function() {
        console.group('🔍 检查JavaScript对象');
        
        const objects = [
            'DemucsApp',
            'DemucsUtils', 
            'DemucsAPI',
            'DemucsSSE',
            'AudioProcessor',
            'showMessage',
            'updateProgress'
        ];
        
        objects.forEach(name => {
            if (window[name]) {
                console.log(`✅ ${name}:`, typeof window[name], window[name]);
            } else {
                console.error(`❌ ${name}: 未定义`);
            }
        });
        
        console.groupEnd();
    },
    
    // 测试进度条
    testProgress: function() {
        console.group('🧪 测试进度条');
        
        const steps = [0, 25, 50, 75, 100];
        let i = 0;
        
        const testInterval = setInterval(() => {
            if (i >= steps.length) {
                clearInterval(testInterval);
                console.log('进度条测试完成');
                console.groupEnd();
                return;
            }
            
            const progress = steps[i];
            console.log(`测试进度: ${progress}%`);
            
            if (window.updateProgress) {
                window.updateProgress(progress, `测试进度 ${progress}%`);
            } else {
                console.error('updateProgress函数不可用');
            }
            
            i++;
        }, 1000);
        
        return testInterval;
    },
    
    // 测试消息显示
    testMessages: function() {
        console.group('🧪 测试消息显示');
        
        const messages = [
            { text: '这是一个信息消息', type: 'info' },
            { text: '这是一个成功消息', type: 'success' },
            { text: '这是一个警告消息', type: 'warning' },
            { text: '这是一个错误消息', type: 'error' }
        ];
        
        messages.forEach((msg, index) => {
            setTimeout(() => {
                console.log(`显示${msg.type}消息:`, msg.text);
                if (window.showMessage) {
                    window.showMessage(msg.text, msg.type);
                } else {
                    console.error('showMessage函数不可用');
                }
            }, index * 1500);
        });
        
        console.groupEnd();
    },
    
    // 模拟文件选择
    simulateFileSelection: function() {
        console.group('🧪 模拟文件选择');
        
        const fileInput = document.getElementById('audioFile');
        if (!fileInput) {
            console.error('文件输入元素未找到');
            console.groupEnd();
            return;
        }
        
        // 创建模拟文件
        const mockFile = new File(['mock audio data'], 'test-audio.mp3', {
            type: 'audio/mp3',
            lastModified: Date.now()
        });
        
        // 创建新的文件列表
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(mockFile);
        fileInput.files = dataTransfer.files;
        
        // 触发change事件
        const changeEvent = new Event('change', { bubbles: true });
        fileInput.dispatchEvent(changeEvent);
        
        console.log('模拟文件选择完成:', mockFile);
        console.groupEnd();
    },
    
    // 运行所有检查
    runAllChecks: function() {
        console.log('🚀 开始调试检查...');
        
        this.checkElements();
        this.checkObjects();
        
        // 等待一秒后运行测试
        setTimeout(() => {
            this.testMessages();
        }, 1000);
        
        setTimeout(() => {
            this.testProgress();
        }, 3000);
        
        console.log('调试检查完成，查看控制台输出');
    },
    
    // 检查API连接
    checkAPI: async function() {
        console.group('🔍 检查API连接');
        
        try {
            console.log('测试健康检查API...');
            const healthResponse = await fetch('/health');
            const healthData = await healthResponse.json();
            console.log('✅ 健康检查:', healthData);
            
            console.log('测试模型列表API...');
            const modelsResponse = await fetch('/api/models');
            const modelsData = await modelsResponse.json();
            console.log('✅ 模型列表:', modelsData);
            
        } catch (error) {
            console.error('❌ API连接失败:', error);
        }
        
        console.groupEnd();
    },
    
    // 调试进度条功能
    debugProgress: function() {
        console.group('🔧 调试进度条功能');
        
        // 检查进度条元素
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        console.log('进度条元素检查:');
        console.log('progressContainer:', progressContainer);
        console.log('progressFill:', progressFill);
        console.log('progressText:', progressText);
        
        if (!progressContainer || !progressFill || !progressText) {
            console.error('❌ 进度条元素缺失！');
            console.groupEnd();
            return false;
        }
        
        // 显示进度条
        console.log('显示进度条...');
        progressContainer.style.display = 'block';
        
        // 测试进度条更新
        const testProgress = [0, 25, 50, 75, 100];
        let i = 0;
        
        const testInterval = setInterval(() => {
            if (i >= testProgress.length) {
                clearInterval(testInterval);
                console.log('✅ 进度条测试完成');
                console.groupEnd();
                return;
            }
            
            const progress = testProgress[i];
            console.log(`设置进度: ${progress}%`);
            
            // 直接更新进度条
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `测试进度 ${progress}%`;
            
            // 也测试updateProgress函数
            if (window.updateProgress) {
                console.log('调用window.updateProgress');
                window.updateProgress(progress, `测试进度 ${progress}%`);
            }
            
            i++;
        }, 1000);
        
        console.groupEnd();
        return testInterval;
    },
    
    // 快速测试进度条可见性
    showProgress: function(progress = 50, message = '测试进度') {
        console.log(`🎯 快速设置进度: ${progress}% - ${message}`);
        
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressContainer && progressFill && progressText) {
            progressContainer.style.display = 'block';
            progressFill.style.width = `${progress}%`;
            progressText.textContent = message;
            console.log('✅ 进度条已更新');
        } else {
            console.error('❌ 进度条元素不存在');
        }
    },
    
    // 隐藏进度条
    hideProgress: function() {
        const progressContainer = document.getElementById('progressContainer');
        if (progressContainer) {
            progressContainer.style.display = 'none';
            console.log('✅ 进度条已隐藏');
        }
    }
};

// 页面加载完成后自动运行基础检查
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        console.log('🔧 调试模式已启用');
        console.log('运行 DemucsDebug.runAllChecks() 来进行完整检查');
        console.log('运行 DemucsDebug.checkAPI() 来检查API连接');
        
        // 自动运行基础检查
        window.DemucsDebug.checkElements();
        window.DemucsDebug.checkObjects();
    }, 1000);
}); 