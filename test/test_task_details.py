#!/usr/bin/env python3
"""
任务详情功能测试脚本

测试管理面板的任务详情查看功能
"""

import requests
import time
import os
import json

# 测试配置
TEST_HOST = "http://localhost:8080"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def test_task_details():
    """测试任务详情功能"""
    print("🧪 任务详情功能测试")
    print("=" * 50)
    
    # 创建会话
    session = requests.Session()
    
    # 1. 管理员登录
    print("\n1. 🔐 管理员登录测试...")
    login_data = {
        'username': ADMIN_USERNAME,
        'password': ADMIN_PASSWORD
    }
    
    login_response = session.post(f'{TEST_HOST}/admin/login', data=login_data)
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return False
    
    print("✅ 管理员登录成功")
    
    # 2. 获取任务列表
    print("\n2. 📋 获取任务列表...")
    tasks_response = session.get(f'{TEST_HOST}/admin/api/files')
    
    if tasks_response.status_code != 200:
        print(f"❌ 获取任务列表失败: {tasks_response.status_code}")
        return False
    
    tasks_data = tasks_response.json()
    if tasks_data['status'] != 'success':
        print(f"❌ 任务列表API返回错误: {tasks_data.get('message', '未知错误')}")
        return False
    
    tasks = tasks_data['data']['tasks']
    print(f"✅ 获取到 {len(tasks)} 个任务")
    
    if not tasks:
        print("⚠️ 没有可测试的任务，请先运行音频分离任务")
        return True
    
    # 3. 测试任务详情API
    print("\n3. 🔍 测试任务详情API...")
    
    for i, task in enumerate(tasks[:3]):  # 只测试前3个任务
        task_id = task['task_id']
        print(f"\n测试任务 {i+1}: {task_id[:8]}...")
        
        # 获取任务详情
        details_response = session.get(f'{TEST_HOST}/admin/api/tasks/{task_id}/details')
        
        if details_response.status_code == 200:
            details_data = details_response.json()
            if details_data['status'] == 'success':
                task_details = details_data['data']
                
                print(f"  ✅ 任务详情获取成功")
                print(f"     任务ID: {task_details['task_id']}")
                print(f"     状态: {task_details['status']}")
                print(f"     输入文件: {len(task_details['input_files'])} 个")
                print(f"     输出文件: {len(task_details['output_files'])} 个")
                print(f"     总大小: {task_details['total_size']} 字节")
                print(f"     创建时间: {time.ctime(task_details['created_time'])}")
                
                # 检查文件路径
                all_files = task_details['input_files'] + task_details['output_files']
                for file_info in all_files[:2]:  # 只检查前2个文件
                    print(f"     文件: {file_info['name']}")
                    print(f"     路径: {file_info['path']}")
                    print(f"     大小: {file_info['size']} 字节")
                    
                    # 验证文件路径格式
                    if file_info['path'].startswith('/demucs/'):
                        print(f"     ✅ 路径格式正确")
                    else:
                        print(f"     ⚠️ 路径格式可能不正确")
                
            else:
                print(f"  ❌ 任务详情获取失败: {details_data.get('message', '未知错误')}")
        
        elif details_response.status_code == 404:
            print(f"  ⚠️ 任务不存在或已被删除")
        
        else:
            print(f"  ❌ 请求失败: {details_response.status_code}")
    
    # 4. 测试不存在的任务
    print("\n4. 🚫 测试不存在的任务...")
    fake_task_id = "non-existent-task-id"
    fake_response = session.get(f'{TEST_HOST}/admin/api/tasks/{fake_task_id}/details')
    
    if fake_response.status_code == 404:
        print("✅ 不存在任务返回404，符合预期")
    else:
        print(f"❌ 不存在任务应返回404，实际返回: {fake_response.status_code}")
    
    print("\n" + "=" * 50)
    print("🎉 任务详情功能测试完成")
    return True

def test_ui_access():
    """测试UI访问"""
    print("\n🌐 UI访问测试")
    print("-" * 30)
    
    # 测试管理面板页面
    try:
        response = requests.get(f'{TEST_HOST}/admin', allow_redirects=False)
        if response.status_code in [200, 302]:  # 200正常访问，302重定向到登录
            print("✅ 管理面板页面可访问")
        else:
            print(f"❌ 管理面板页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 管理面板访问错误: {e}")
    
    # 测试静态文件
    try:
        css_response = requests.get(f'{TEST_HOST}/static/css/main.css')
        if css_response.status_code == 200:
            print("✅ CSS文件加载正常")
        else:
            print(f"❌ CSS文件加载失败: {css_response.status_code}")
    except Exception as e:
        print(f"❌ CSS文件访问错误: {e}")

if __name__ == "__main__":
    print("🚀 开始任务详情功能测试")
    print(f"测试服务器: {TEST_HOST}")
    
    # 检查服务器状态
    try:
        health_response = requests.get(f'{TEST_HOST}/health', timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"❌ 服务器状态异常: {health_response.status_code}")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print("请确保服务器正在运行在 http://localhost:8080")
        exit(1)
    
    # 运行测试
    try:
        test_ui_access()
        success = test_task_details()
        
        if success:
            print("\n🎊 所有测试通过！")
            exit(0)
        else:
            print("\n💥 部分测试失败")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n⏸️ 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n💥 测试过程中发生错误: {e}")
        exit(1) 