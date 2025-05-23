# 测试使用指南

这是Demucs音频分离应用的完整测试指南。

## 📁 目录结构

```
test/
├── README.md                      # 测试目录总览
├── TESTING_GUIDE.md               # 本文档 - 详细使用指南
├── test_suite.py                  # 高级测试套件管理器
├── run_tests.py                   # 基础测试运行器
├── test_files.md                  # 测试文件说明
├── test.mp3                       # 测试音频文件
│
├── unit/                          # 单元测试
│   ├── __init__.py
│   ├── test_api.py               # API接口测试
│   ├── test_demucs.py            # Demucs核心功能测试
│   ├── test_fixed_separator.py   # 音频分离器修复测试
│   ├── test_full_app.py          # 全应用集成测试
│   ├── test_ffmpeg_compatibility.py # FFmpeg兼容性测试
│   └── test_progress_feedback.py # 进度反馈测试
│
├── integration/                   # 集成测试 (规划中)
│   └── __init__.py
│
├── mcp/                          # MCP协议测试
│   ├── README.md
│   └── client.py
│
├── output/                       # 测试输出文件
│   └── *.wav
│
└── fixtures/                     # 测试数据 (规划中)
```

## 🚀 快速开始

### 方式1: 使用高级测试套件管理器 (推荐)

```bash
# 切换到项目根目录
cd /path/to/demucs

# 列出所有可用测试
python test/test_suite.py --action list

# 验证测试环境
python test/test_suite.py --action validate

# 运行所有测试
python test/test_suite.py

# 只运行单元测试
python test/test_suite.py --category unit

# 运行特定测试
python test/test_suite.py --test api
```

### 方式2: 使用基础测试运行器

```bash
# 运行所有测试
python test/run_tests.py

# 运行特定类型测试
python test/run_tests.py --test api
python test/run_tests.py --test demucs

# 运行特定类别测试
python test/run_tests.py --category unit
```

### 方式3: 直接运行单个测试文件

```bash
cd test
python unit/test_demucs.py
python unit/test_api.py
```

## 📋 测试模块详解

### 1. 核心功能测试

#### `test_demucs.py` - Demucs核心功能
```bash
# 运行Demucs基础功能测试
python test/test_suite.py --test demucs
```

**测试内容:**
- 模型加载验证
- 音频文件处理
- 基本分离功能
- 设备兼容性 (CPU/GPU)

#### `test_fixed_separator.py` - 分离器修复验证
```bash
# 测试分离器修复
python test/test_suite.py --test fixed_separator
```

**测试内容:**
- 维度不匹配修复
- 参数命名修复
- 错误处理机制

#### `test_full_app.py` - 完整应用测试
```bash
# 完整应用流程测试
python test/test_suite.py --test full_app
```

**测试内容:**
- 端到端工作流
- 服务集成
- 文件管理
- 错误恢复

### 2. 兼容性测试

#### `test_ffmpeg_compatibility.py` - FFmpeg兼容性
```bash
# FFmpeg兼容性测试
python test/test_suite.py --test ffmpeg_compatibility
```

**测试内容:**
- FFmpeg库加载
- 符号链接创建
- 路径解析
- 版本兼容性

#### `test_progress_feedback.py` - 进度反馈
```bash
# 进度反馈机制测试
python test/test_suite.py --test progress_feedback
```

**测试内容:**
- 进度回调函数
- 实时进度更新
- 错误状态处理

### 3. 接口测试

#### `test_api.py` - HTTP API测试
```bash
# API接口测试 (需要服务器运行)
python ../run.py &  # 启动服务器
python test/test_suite.py --test api
```

**测试内容:**
- REST API端点
- 文件上传/下载
- 错误响应
- 认证机制

## ⚙️ 测试配置

### 环境变量配置

```bash
# 设置测试服务器地址
export TEST_SERVER_URL="http://127.0.0.1:8080"

# 设置测试超时时间
export TEST_TIMEOUT=300

# 设置测试设备
export TEST_DEVICE="cpu"  # 或 "cuda"

# 设置测试详细程度
export TEST_VERBOSITY=2
```

### 测试参数自定义

在测试文件中可以修改以下参数：

```python
# 测试配置示例
TEST_CONFIG = {
    'device': 'cpu',                    # 计算设备
    'model_name': 'htdemucs',          # 默认模型
    'sample_rate': 44100,              # 采样率
    'channels': 2,                     # 声道数
    'stems': ['vocals', 'drums', 'bass', 'other'],  # 分离轨道
    'timeout': 300,                    # 超时时间
    'max_file_size': 50 * 1024 * 1024, # 最大文件大小 (50MB)
}
```

## 🔧 高级用法

### 1. 自定义测试过滤

```bash
# 只运行包含"api"的测试
python test/test_suite.py --test api

# 运行特定类别的所有测试
python test/test_suite.py --category unit

# 组合过滤
python test/run_tests.py --category unit --test demucs
```

### 2. 并行测试执行

```bash
# 使用pytest进行并行测试 (需要安装pytest-xdist)
pip install pytest pytest-xdist
pytest test/unit/ -n auto
```

### 3. 测试覆盖率分析

```bash
# 安装覆盖率工具
pip install coverage

# 运行覆盖率测试
coverage run --source=app test/test_suite.py
coverage report
coverage html  # 生成HTML报告
```

### 4. 性能基准测试

```bash
# 使用内置时间测量
python test/test_suite.py --verbosity 2

# 使用专业基准测试工具
pip install pytest-benchmark
pytest test/unit/test_demucs.py --benchmark-only
```

## 🐛 故障排除

### 常见问题及解决方案

#### 1. 模块导入错误
```
ImportError: No module named 'app'
```

**解决方案:**
```bash
# 确保在项目根目录运行测试
cd /path/to/demucs
python test/test_suite.py

# 或者设置PYTHONPATH
export PYTHONPATH=/path/to/demucs:$PYTHONPATH
```

#### 2. 测试音频文件缺失
```
❌ 缺少测试音频文件: test.mp3
```

**解决方案:**
```bash
# 下载测试音频文件
wget -O test/test.mp3 "https://example.com/test-audio.mp3"

# 或者使用任意短音频文件
cp /path/to/any/audio.mp3 test/test.mp3
```

#### 3. API测试失败
```
ConnectionError: Failed to establish connection
```

**解决方案:**
```bash
# 确保应用服务器正在运行
python run.py &

# 等待服务器启动
sleep 5

# 验证服务器状态
curl http://127.0.0.1:8080/api/models
```

#### 4. 内存不足错误
```
RuntimeError: CUDA out of memory
```

**解决方案:**
```bash
# 强制使用CPU
export TEST_DEVICE=cpu

# 或在测试中降低配置
# 修改测试文件中的配置参数
```

#### 5. 权限错误
```
PermissionError: [Errno 13] Permission denied
```

**解决方案:**
```bash
# 确保输出目录有写权限
chmod 755 test/output/

# 清理可能的权限问题文件
sudo rm -rf test/output/*
```

### 调试技巧

#### 1. 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 单步调试
```python
import pdb
pdb.set_trace()  # 在测试中设置断点
```

#### 3. 保留测试文件
```python
# 在测试清理方法中添加
def tearDown(self):
    if os.getenv('KEEP_TEST_FILES'):
        return  # 跳过清理
    # 正常清理逻辑...
```

使用方式:
```bash
KEEP_TEST_FILES=1 python test/test_suite.py
```

## 📊 测试报告

### 标准输出格式

```
🧪 开始运行测试...
============================================================
✅ 加载测试模块: unit.test_demucs

test_model_loading (unit.test_demucs.TestDemucs) ... ok
test_audio_processing (unit.test_demucs.TestDemucs) ... ok

============================================================
📊 测试执行总结
============================================================
🔢 运行测试数: 2
✅ 成功测试数: 2
❌ 失败测试数: 0
🔴 错误测试数: 0

🎉 所有测试通过!
```

### 生成详细报告

```bash
# 生成HTML测试报告
python test/test_suite.py --verbosity 2 > test_report.txt

# 生成JUnit XML报告 (需要pytest)
pytest test/unit/ --junit-xml=test_report.xml

# 生成覆盖率报告
coverage run test/test_suite.py
coverage html
```

## 📈 持续集成

### GitHub Actions配置示例

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Validate test environment
      run: python test/test_suite.py --action validate
    
    - name: Run tests
      run: python test/test_suite.py --category unit
```

### 本地CI脚本

```bash
#!/bin/bash
# ci_test.sh - 本地持续集成脚本

set -e

echo "🔧 验证测试环境..."
python test/test_suite.py --action validate

echo "📋 列出可用测试..."
python test/test_suite.py --action list

echo "🧪 运行所有测试..."
python test/test_suite.py

echo "📊 生成覆盖率报告..."
coverage run test/test_suite.py
coverage report

echo "✅ CI测试完成!"
```

## 🎯 最佳实践

### 1. 测试编写规范

- **命名规范**: `test_<功能描述>`
- **文档字符串**: 每个测试方法都应有清晰的文档
- **独立性**: 测试之间不应有依赖关系
- **可重复性**: 测试结果应该是确定的

### 2. 测试数据管理

```python
# 使用fixtures目录存放测试数据
TEST_DATA_DIR = Path(__file__).parent / "fixtures"

# 使用临时文件避免污染
import tempfile
with tempfile.TemporaryDirectory() as temp_dir:
    # 测试逻辑...
```

### 3. 资源清理

```python
def tearDown(self):
    """测试后清理资源"""
    # 清理临时文件
    if hasattr(self, 'temp_files'):
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.remove(file_path)
```

### 4. 错误处理测试

```python
def test_error_handling(self):
    """测试错误处理机制"""
    with self.assertRaises(ValueError):
        # 应该抛出错误的操作
        invalid_operation()
```

通过遵循这个指南，你可以有效地运行、调试和维护Demucs音频分离应用的测试套件。

## 💻 使用方法

### 1. 快速验证（推荐新手）

```bash
cd test
python quick_test.py
```

快速验证脚本会依次执行：
- 环境检查 (Python版本、依赖包、测试文件)
- 基本导入测试 (Flask应用、AudioSeparator、FileManager)
- 模型加载测试 (所有Demucs模型)
- API服务器连接测试
- 音频处理验证

### 2. 基础测试运行器

运行所有测试：
```bash
python run_tests.py
```

运行特定测试类型：
```bash
python run_tests.py --test api          # API接口测试
python run_tests.py --test download     # 下载功能测试
python run_tests.py --test demucs       # Demucs核心功能
python run_tests.py --test ffmpeg       # FFmpeg兼容性
python run_tests.py --test progress     # 进度反馈
python run_tests.py --test separator    # 音频分离器
python run_tests.py --test full         # 完整应用测试
```

运行特定测试类别：
```bash
python run_tests.py --category unit        # 单元测试
python run_tests.py --category integration # 集成测试
python run_tests.py --category mcp         # MCP协议测试
``` 