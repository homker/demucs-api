#!/usr/bin/env python3
"""
测试进度条修复效果
"""

import requests
import time
import json

def test_progress_fix():
    """测试进度条修复效果"""
    print("🧪 测试进度条修复效果")
    
    # 1. 检查服务器状态
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        print(f"✅ 服务器状态: {response.json()}")
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False
    
    # 2. 启动音频分离任务
    try:
        with open("test/fixtures/test_audio.wav", "rb") as f:
            files = {"audio": f}
            data = {
                "model": "htdemucs",
                "stems": "vocals,drums"
            }
            response = requests.post("http://localhost:8080/api/process", files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 任务启动成功: {result}")
            job_id = result["data"]["job_id"]
            
            # 3. 监控进度
            print(f"📊 开始监控任务进度: {job_id}")
            progress_url = f"http://localhost:8080/api/progress/{job_id}"
            
            # 测试SSE连接
            print(f"🔗 SSE URL: {progress_url}")
            
            # 简单的进度检查
            for i in range(5):
                try:
                    # 使用curl测试SSE连接
                    import subprocess
                    result = subprocess.run([
                        "curl", "-s", "--max-time", "3", progress_url
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0 and result.stdout:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.startswith('data: '):
                                data_str = line[6:]  # 去掉 'data: '
                                try:
                                    data = json.loads(data_str)
                                    print(f"📈 进度更新: {data.get('progress', 'N/A')}% - {data.get('message', 'N/A')}")
                                except json.JSONDecodeError:
                                    print(f"📄 原始数据: {data_str}")
                    else:
                        print(f"⚠️ SSE连接问题: {result.stderr}")
                        
                except Exception as e:
                    print(f"❌ 进度检查失败: {e}")
                
                time.sleep(2)
            
            return True
        else:
            print(f"❌ 任务启动失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_progress_fix()
    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}") 