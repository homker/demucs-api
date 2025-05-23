# Demucs 测试目录

本目录包含了 Demucs 音频分离应用的所有测试代码。测试按功能和类型进行组织，确保代码质量和功能正确性。

## 📁 目录结构

```
test/
├── unit/                    # 单元测试
│   ├── test_admin_panel.py     # 管理面板功能测试（包含性能测试）
│   ├── test_api.py            # API接口测试（包含基础端点测试）
│   ├── test_audio_format_quality.py  # 音频格式和质量测试
│   ├── test_demucs.py         # Demucs核心功能测试
│   ├── test_download_functionality.py  # 下载功能测试
│   ├── test_ffmpeg_compatibility.py   # FFmpeg兼容性测试
│   ├── test_fixed_separator.py        # 音频分离器测试
│   ├── test_full_app.py      # 完整应用测试
│   └── test_progress_feedback.py      # 进度反馈测试
├── integration/             # 集成测试
│   ├── test_api_response_format.py    # API响应格式集成测试
│   └── test_frontend_integration.py  # 前端功能集成测试
├── mcp/                     # MCP协议测试
│   ├── client.py            # MCP客户端测试
│   └── README.md           # MCP测试说明
├── fixtures/                # 测试固定数据
├── output/                  # 测试输出目录
├── run_tests.py             # 测试运行器
├── test_suite.py           # 测试套件
├── quick_test.py           # 快速测试脚本
└── README.md               # 本文件
```

## 🚀 快速开始

### 运行所有测试
```bash
# 在项目根目录运行
cd test
python run_tests.py --test all
```

### 运行特定类型的测试
```bash
# 只运行单元测试
python run_tests.py --category unit

# 只运行集成测试
python run_tests.py --category integration

# 只运行MCP协议测试
python run_tests.py --category mcp

# 运行特定功能测试
python run_tests.py --test admin      # 管理面板测试
python run_tests.py --test api        # API测试
python run_tests.py --test frontend   # 前端测试
```

### 运行单个测试文件
```bash
# 运行管理面板测试
python unit/test_admin_panel.py

# 运行API响应格式测试
python integration/test_api_response_format.py

# 运行前端集成测试
python integration/test_frontend_integration.py
```

## 📊 测试类型说明

### 单元测试 (unit/)
测试单个模块或功能的正确性，包括：

- **test_admin_panel.py**: 管理面板功能和性能测试
  - 登录/登出功能
  - 文件扫描性能
  - 任务管理
  - 权限控制

- **test_api.py**: API接口完整测试
  - 基础端点测试
  - 字段名兼容性
  - 错误处理
  - 文件上传处理

- **test_audio_format_quality.py**: 音频格式和质量测试
  - 支持的音频格式
  - 音质选项
  - 格式转换

### 集成测试 (integration/)
测试多个组件之间的交互，包括：

- **test_api_response_format.py**: API响应格式集成测试
  - 成功响应格式验证
  - 错误响应格式验证
  - 前端兼容性检查
  - 响应头测试

- **test_frontend_integration.py**: 前端功能集成测试
  - 页面访问测试
  - JavaScript文件加载
  - CSS文件加载
  - API端点集成
  - 错误页面测试

### MCP协议测试 (mcp/)
测试MCP (Model Context Protocol) 相关功能。

## 🛠️ 测试配置

### 服务器要求
- 测试服务器应在 `http://localhost:8080` 运行
- 管理员账号: `admin` / `admin123`

### 测试数据
- 测试音频文件: `test/fixtures/test.mp3`
- 测试输出目录: `test/output/`

## 📋 测试报告

测试运行器会生成详细的测试报告，包括：
- 执行时间
- 成功/失败统计
- 性能指标
- 错误详情

```bash
# 生成JSON格式的测试报告
python run_tests.py --output test_report.json
```

## 🔧 开发指南

### 添加新测试
1. 根据功能类型选择合适的目录 (unit/integration/mcp)
2. 创建新的测试文件或在现有文件中添加测试方法
3. 更新 `run_tests.py` 以包含新测试
4. 更新本README文档

### 测试命名规范
- 测试文件: `test_<功能名>.py`
- 测试类: `Test<功能名>`
- 测试方法: `test_<具体功能>()`

### 测试编写原则
1. 每个测试应该独立可运行
2. 使用清晰的断言和错误消息
3. 适当的测试数据清理
4. 包含性能测试（如适用）

## 📈 最近更新

### 2024年测试重组
- ✅ 将根目录测试脚本重组到对应测试目录
- ✅ 合并 `test_admin_performance.py` 到 `unit/test_admin_panel.py`
- ✅ 合并 `test_api.py` 到 `unit/test_api.py`
- ✅ 移动 `test_api_response_format.py` 到 `integration/`
- ✅ 移动 `test_frontend_fix.py` 到 `integration/test_frontend_integration.py`
- ✅ 更新测试运行器以支持新的测试结构

## 💡 常见问题

### Q: 测试失败怎么办？
A: 
1. 检查服务器是否正在运行
2. 确认测试数据文件存在
3. 查看详细错误信息
4. 检查网络连接和端口

### Q: 如何跳过某些测试？
A: 使用unittest的skip装饰器或在测试中调用skipTest()

### Q: 如何增加测试覆盖率？
A: 
1. 使用coverage工具分析代码覆盖率
2. 添加边界条件测试
3. 增加错误场景测试

## 📞 支持

如有问题，请参考：
- 项目文档: `docs/`
- 测试指南: `test/TESTING_GUIDE.md`
- 问题报告: GitHub Issues 