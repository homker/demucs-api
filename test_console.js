// 控制台测试脚本
// 在浏览器控制台中运行这个脚本来测试修复效果

// 1. 测试模拟完成数据
console.log('=== 测试1: 模拟完成任务 ===');
const mockCompletedData = {
    job_id: '238f45cb-41fc-471a-8bae-466477460030',
    progress: 100,
    status: 'completed',
    message: '音频分离完成，格式: MP3，质量: low',
    result_file: '/path/to/result.zip'
};

console.log('调用showResults with mock data...');
window.AudioProcessor.showResults(mockCompletedData);

// 2. 测试从API获取真实数据
setTimeout(async () => {
    console.log('\n=== 测试2: 从API获取真实数据 ===');
    try {
        const response = await fetch('/api/status/238f45cb-41fc-471a-8bae-466477460030');
        const result = await response.json();
        
        if (result.status === 'success') {
            console.log('API返回的数据:', result.data);
            console.log('调用showResults with API data...');
            window.AudioProcessor.showResults(result.data);
        } else {
            console.error('API返回错误:', result);
        }
    } catch (error) {
        console.error('API调用失败:', error);
    }
}, 2000);

// 3. 测试无结果文件的情况
setTimeout(() => {
    console.log('\n=== 测试3: 无结果文件 ===');
    const noFileData = {
        job_id: '238f45cb-41fc-471a-8bae-466477460030',
        progress: 100,
        status: 'completed',
        message: '音频分离完成，但没有文件信息'
        // 注意：没有 result_file 字段
    };
    
    console.log('调用showResults without result_file...');
    window.AudioProcessor.showResults(noFileData);
}, 4000); 