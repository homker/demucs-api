#!/usr/bin/env python3
"""
管理面板功能测试模块
Tests admin panel functionality including authentication and file management
"""

import unittest
import requests
import time
import os
import json

class TestAdminPanel(unittest.TestCase):
    """管理面板测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.api_base = "http://127.0.0.1:8080"
        cls.admin_username = "admin"
        cls.admin_password = "admin123"
        cls.session = requests.Session()
    
    def test_admin_login_success(self):
        """测试管理员登录成功"""
        print("\n🔐 测试管理员登录...")
        
        # 测试登录
        login_data = {
            'username': self.admin_username,
            'password': self.admin_password
        }
        
        response = self.session.post(f"{self.api_base}/admin/login", data=login_data)
        
        # 登录成功会重定向
        self.assertEqual(response.status_code, 200)
        
        # 验证是否能访问管理面板
        admin_response = self.session.get(f"{self.api_base}/admin/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertIn("管理面板", admin_response.text)
        
        print("✅ 管理员登录成功")
    
    def test_admin_login_failure(self):
        """测试错误登录"""
        print("\n❌ 测试错误登录...")
        
        # 使用错误密码
        login_data = {
            'username': self.admin_username,
            'password': "wrong_password"
        }
        
        response = requests.post(f"{self.api_base}/admin/login", data=login_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("用户名或密码错误", response.text)
        
        print("✅ 错误登录正确被拒绝")
    
    def test_admin_access_protection(self):
        """测试管理面板访问保护"""
        print("\n🛡️ 测试访问保护...")
        
        # 未登录直接访问管理面板
        response = requests.get(f"{self.api_base}/admin/")
        
        # 应该重定向到登录页面
        self.assertEqual(response.status_code, 200)
        # 检查是否包含登录表单
        self.assertTrue(
            "请输入管理员账号密码" in response.text or 
            "login" in response.url or
            "用户名" in response.text
        )
        
        print("✅ 未授权访问被正确重定向")
    
    def test_admin_files_api(self):
        """测试文件列表API - 新的任务视图"""
        print("\n📁 测试任务列表API...")
        
        # 先登录
        login_data = {
            'username': self.admin_username,
            'password': self.admin_password
        }
        self.session.post(f"{self.api_base}/admin/login", data=login_data)
        
        # 获取任务列表
        response = self.session.get(f"{self.api_base}/admin/api/files")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # 验证新的数据结构
        file_data = data['data']
        self.assertIn('tasks', file_data)
        self.assertIn('orphaned_files', file_data)
        self.assertIn('summary', file_data)
        
        # 验证摘要数据
        summary = file_data['summary']
        self.assertIn('total_tasks', summary)
        self.assertIn('completed_tasks', summary)
        self.assertIn('processing_tasks', summary)
        self.assertIn('old_tasks', summary)
        self.assertIn('total_size', summary)
        self.assertIn('orphaned_files_count', summary)
        
        print(f"✅ 任务列表API正常，共{summary['total_tasks']}个任务，{summary['orphaned_files_count']}个孤立文件")
    
    def test_admin_task_delete(self):
        """测试删除任务功能"""
        print("\n🗑️ 测试删除任务功能...")
        
        # 先登录
        login_data = {
            'username': self.admin_username,
            'password': self.admin_password
        }
        self.session.post(f"{self.api_base}/admin/login", data=login_data)
        
        # 获取任务列表
        files_response = self.session.get(f"{self.api_base}/admin/api/files")
        file_data = files_response.json()['data']
        
        if file_data['tasks']:
            # 尝试删除第一个任务
            task_id = file_data['tasks'][0]['task_id']
            
            delete_response = self.session.post(f"{self.api_base}/admin/api/tasks/delete", 
                                              json={'task_id': task_id})
            self.assertEqual(delete_response.status_code, 200)
            
            delete_data = delete_response.json()
            self.assertEqual(delete_data['status'], 'success')
            print(f"✅ 任务删除成功: {delete_data['message']}")
        else:
            print("✅ 没有任务可删除，跳过测试")
    
    def test_admin_cleanup_old_files(self):
        """测试清理过期文件功能"""
        print("\n🧹 测试清理过期文件...")
        
        # 先登录
        login_data = {
            'username': self.admin_username,
            'password': self.admin_password
        }
        self.session.post(f"{self.api_base}/admin/login", data=login_data)
        
        # 获取清理前的统计
        files_before = self.session.get(f"{self.api_base}/admin/api/files")
        summary_before = files_before.json()['data']['summary']
        old_files_before = summary_before['old_files_count']
        
        # 执行清理
        cleanup_response = self.session.post(f"{self.api_base}/admin/api/cleanup/old")
        self.assertEqual(cleanup_response.status_code, 200)
        
        cleanup_data = cleanup_response.json()
        self.assertEqual(cleanup_data['status'], 'success')
        
        # 获取清理后的统计
        files_after = self.session.get(f"{self.api_base}/admin/api/files")
        summary_after = files_after.json()['data']['summary']
        old_files_after = summary_after['old_files_count']
        
        # 过期文件数量应该减少
        self.assertLessEqual(old_files_after, old_files_before)
        
        print(f"✅ 清理完成：过期文件从 {old_files_before} 个减少到 {old_files_after} 个")
    
    def test_admin_logout(self):
        """测试退出登录"""
        print("\n🚪 测试退出登录...")
        
        # 先登录
        login_data = {
            'username': self.admin_username,
            'password': self.admin_password
        }
        self.session.post(f"{self.api_base}/admin/login", data=login_data)
        
        # 确认可以访问管理面板
        admin_response = self.session.get(f"{self.api_base}/admin/")
        self.assertEqual(admin_response.status_code, 200)
        
        # 退出登录
        logout_response = self.session.get(f"{self.api_base}/admin/logout")
        
        # 再次尝试访问管理面板，应该被重定向到登录页
        admin_response_after = self.session.get(f"{self.api_base}/admin/")
        self.assertTrue(
            "请输入管理员账号密码" in admin_response_after.text or
            "用户名" in admin_response_after.text
        )
        
        print("✅ 退出登录成功")

def run_admin_tests():
    """运行管理面板测试的函数入口"""
    print("🛠️ 管理面板功能测试")
    print("="*50)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAdminPanel)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print("\n" + "="*50)
    print("📊 管理面板测试结果总结:")
    print(f"   运行测试数: {result.testsRun}")
    print(f"   失败数: {len(result.failures)}")
    print(f"   错误数: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 所有管理面板测试通过!")
        return True
    else:
        print("\n⚠️ 部分管理面板测试失败")
        return False

if __name__ == "__main__":
    # 直接运行时的测试
    run_admin_tests() 