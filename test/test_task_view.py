#!/usr/bin/env python3
"""
测试任务视图功能的演示脚本
用于创建示例任务和文件，验证管理面板的任务分组功能
"""

import os
import time
import shutil
import requests

def create_test_files():
    """创建一些示例文件来模拟任务"""
    
    print("🎯 创建示例任务文件...")
    
    # 创建上传和输出目录
    upload_dir = "../uploads"
    output_dir = "../outputs"
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 模拟3个任务
    tasks = [
        {"id": "abc12345", "name": "song1"},
        {"id": "def67890", "name": "song2"}, 
        {"id": "ghi54321", "name": "music"},
    ]
    
    for task in tasks:
        task_id = task["id"]
        name = task["name"]
        
        # 创建上传文件
        input_file = f"{upload_dir}/{name}_{task_id}.mp3"
        with open(input_file, 'w') as f:
            f.write(f"# 模拟音频文件 - 任务 {task_id}\n")
        
        # 创建输出目录和文件
        output_task_dir = f"{output_dir}/{task_id}"
        os.makedirs(output_task_dir, exist_ok=True)
        
        stems = ["vocals", "drums", "bass", "other"]
        for stem in stems:
            output_file = f"{output_task_dir}/{name}_{stem}.wav"
            with open(output_file, 'w') as f:
                f.write(f"# 分离的{stem}音轨 - 任务 {task_id}\n")
        
        print(f"  ✅ 创建任务 {task_id}: {name}")
    
    # 创建一些孤立文件
    orphaned_files = [
        f"{upload_dir}/unknown_file.mp3",
        f"{output_dir}/orphaned_vocals.wav"
    ]
    
    for file_path in orphaned_files:
        with open(file_path, 'w') as f:
            f.write("# 孤立文件示例\n")
    
    print(f"  ✅ 创建了 {len(orphaned_files)} 个孤立文件")
    print(f"🎉 示例文件创建完成！")

def test_admin_api():
    """测试管理面板API"""
    
    print("\n🔍 测试管理面板API...")
    
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    login_response = session.post('http://localhost:8080/admin/login', data=login_data)
    print(f"  📋 登录状态: {login_response.status_code}")
    
    # 获取任务数据
    files_response = session.get('http://localhost:8080/admin/api/files')
    
    if files_response.status_code == 200:
        data = files_response.json()
        
        if data['status'] == 'success':
            file_data = data['data']
            summary = file_data['summary']
            
            print(f"  📊 任务统计:")
            print(f"     总任务数: {summary['total_tasks']}")
            print(f"     已完成任务: {summary['completed_tasks']}")
            print(f"     处理中任务: {summary['processing_tasks']}")
            print(f"     过期任务: {summary['old_tasks']}")
            print(f"     孤立文件: {summary['orphaned_files_count']}")
            print(f"     总大小: {summary['total_size']} 字节")
            
            print(f"\n  📋 任务详情:")
            for i, task in enumerate(file_data['tasks'], 1):
                print(f"     任务 {i}: {task['task_id'][:8]}...")
                print(f"       状态: {task['status']}")
                print(f"       输入文件: {len(task['input_files'])} 个")
                print(f"       输出文件: {len(task['output_files'])} 个")
                print(f"       大小: {task['total_size']} 字节")
                print(f"       创建时间: {time.ctime(task['created_time'])}")
                print(f"       是否过期: {'是' if task['is_old'] else '否'}")
                print()
            
            if file_data['orphaned_files']:
                print(f"  📄 孤立文件:")
                for file in file_data['orphaned_files']:
                    print(f"     {file['name']} ({file['type']})")
        else:
            print(f"  ❌ API错误: {data['message']}")
    else:
        print(f"  ❌ 请求失败: {files_response.status_code}")

def test_task_deletion():
    """测试任务删除功能"""
    
    print("\n🗑️ 测试任务删除功能...")
    
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    session.post('http://localhost:8080/admin/login', data=login_data)
    
    # 获取任务列表
    files_response = session.get('http://localhost:8080/admin/api/files')
    data = files_response.json()
    
    if data['status'] == 'success' and data['data']['tasks']:
        # 删除第一个任务
        first_task = data['data']['tasks'][0]
        task_id = first_task['task_id']
        
        print(f"  🎯 删除任务: {task_id[:8]}...")
        
        delete_response = session.post('http://localhost:8080/admin/api/tasks/delete', 
                                     json={'task_id': task_id})
        
        if delete_response.status_code == 200:
            delete_data = delete_response.json()
            if delete_data['status'] == 'success':
                print(f"  ✅ {delete_data['message']}")
            else:
                print(f"  ❌ 删除失败: {delete_data['message']}")
        else:
            print(f"  ❌ 请求失败: {delete_response.status_code}")
    else:
        print("  ℹ️ 没有任务可删除")

def cleanup_test_files():
    """清理测试文件"""
    
    print("\n🧹 清理测试文件...")
    
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    session.post('http://localhost:8080/admin/login', data=login_data)
    
    # 清理所有文件
    cleanup_response = session.post('http://localhost:8080/admin/api/cleanup/all')
    
    if cleanup_response.status_code == 200:
        cleanup_data = cleanup_response.json()
        if cleanup_data['status'] == 'success':
            print(f"  ✅ {cleanup_data['message']}")
        else:
            print(f"  ❌ 清理失败: {cleanup_data['message']}")
    else:
        print(f"  ❌ 请求失败: {cleanup_response.status_code}")

def main():
    """主函数"""
    
    print("🎵 管理面板任务视图功能测试")
    print("=" * 50)
    
    try:
        # 1. 创建测试文件
        create_test_files()
        
        # 2. 测试API
        test_admin_api()
        
        # 3. 测试删除功能
        test_task_deletion()
        
        # 4. 再次查看状态
        print("\n🔄 删除后的状态:")
        test_admin_api()
        
        # 5. 清理测试文件（可选）
        print("\n❓ 是否清理测试文件? (y/N):", end=" ")
        if input().lower().startswith('y'):
            cleanup_test_files()
        else:
            print("  📁 保留测试文件，可在管理面板中手动管理")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
    
    print("\n🎉 任务视图测试完成！")
    print("💡 提示: 访问 http://localhost:8080/admin 查看管理面板")

if __name__ == "__main__":
    main() 