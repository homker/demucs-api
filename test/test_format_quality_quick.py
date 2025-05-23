#!/usr/bin/env python3
"""
快速测试音频格式和质量功能 (只测试WAV和MP3)
避免耗时的FLAC无损压缩测试
"""

import requests
import json

def test_api_endpoints():
    """测试API端点"""
    base_url = "http://127.0.0.1:8080"
    
    print("🧪 快速测试音频格式和质量功能 (WAV和MP3)")
    print("📝 注意：为提高测试速度，已跳过FLAC无损压缩测试")
    print("="*60)
    
    # 测试格式API
    print("\n1. 测试获取支持格式...")
    try:
        response = requests.get(f"{base_url}/api/formats")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            formats = data['data']['formats']
            default = data['data']['default']
            print(f"   ✅ 支持格式: {formats}")
            print(f"   ✅ 默认格式: {default}")
            
            # 验证包含WAV和MP3
            if 'wav' in formats and 'mp3' in formats:
                print(f"   ✅ WAV和MP3格式都支持")
            else:
                print(f"   ❌ 缺少WAV或MP3格式支持")
        else:
            print(f"   ❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试质量API
    print("\n2. 测试获取质量选项...")
    try:
        response = requests.get(f"{base_url}/api/qualities")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            qualities = data['data']['qualities']
            default = data['data']['default']
            print(f"   ✅ 质量选项: {list(qualities.keys())}")
            print(f"   ✅ 默认质量: {default}")
            for key, desc in qualities.items():
                print(f"      {key}: {desc}")
        else:
            print(f"   ❌ 请求失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试无效格式
    print("\n3. 测试无效格式处理...")
    try:
        with open('test.mp3', 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'invalid_format',
                'audio_quality': 'high'
            }
            response = requests.post(f"{base_url}/api/process", files=files, data=data)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 400:
                result = response.json()
                print(f"   ✅ 正确拒绝无效格式: {result['message']}")
            else:
                print(f"   ❌ 未正确处理无效格式: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试无效质量
    print("\n4. 测试无效质量处理...")
    try:
        with open('test.mp3', 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'mp3',
                'audio_quality': 'invalid_quality'
            }
            response = requests.post(f"{base_url}/api/process", files=files, data=data)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 400:
                result = response.json()
                print(f"   ✅ 正确拒绝无效质量: {result['message']}")
            else:
                print(f"   ❌ 未正确处理无效质量: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试有效的MP3高质量分离
    print("\n5. 测试MP3高质量分离...")
    try:
        with open('test.mp3', 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'mp3',
                'audio_quality': 'high'
            }
            response = requests.post(f"{base_url}/api/process", files=files, data=data)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                job_id = result['data']['job_id']
                print(f"   ✅ MP3高质量分离任务创建成功: {job_id}")
            else:
                print(f"   ❌ 任务创建失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 测试有效的WAV中等质量分离
    print("\n6. 测试WAV中等质量分离...")
    try:
        with open('test.mp3', 'rb') as f:
            files = {'file': f}
            data = {
                'model': 'htdemucs',
                'stems': 'vocals',
                'output_format': 'wav',
                'audio_quality': 'medium'
            }
            response = requests.post(f"{base_url}/api/process", files=files, data=data)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                job_id = result['data']['job_id']
                print(f"   ✅ WAV中等质量分离任务创建成功: {job_id}")
            else:
                print(f"   ❌ 任务创建失败: {response.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n" + "="*60)
    print("🎉 快速测试完成! (已跳过FLAC无损测试)")
    print("💡 如需完整测试，请运行: python test/run_tests.py --test format")

if __name__ == "__main__":
    test_api_endpoints() 