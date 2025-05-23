# 测试目录结构说明

本目录包含Demucs音频分离应用的完整测试套件。

## 📁 目录结构

```
test/
├── README.md                      # 本文档
├── run_tests.py                   # 测试运行器脚本
├── test_suite.py                  # 高级测试套件管理器
├── quick_test.py                  # 快速验证脚本
├── test.mp3                       # 测试音频文件
├── test_files.md                  # 测试文件使用说明
│
├── unit/                          # 单元测试
│   ├── test_api.py               # API接口测试
│   ├── test_demucs.py            # Demucs核心功能测试
│   ├── test_download_functionality.py # 下载功能测试
│   ├── test_fixed_separator.py   # 音频分离器修复测试
│   ├── test_full_app.py          # 全应用集成测试
│   ├── test_ffmpeg_compatibility.py # FFmpeg兼容性测试
│   └── test_progress_feedback.py # 进度反馈测试
│
├── integration/                   # 集成测试
│   └── (待规划)
│
├── mcp/                          # MCP协议测试
│   ├── README.md                 # MCP测试说明
│   └── client.py                 # MCP客户端测试
│
├── output/                       # 测试输出文件夹
│   └── *.wav                     # 生成的测试音频文件
│
└── fixtures/                     # 测试数据
    └── (测试用数据文件)
```

## 🚀 快速开始

### 1. 运行所有测试
```bash
cd test
python run_tests.py
```

### 2. 运行特定类型测试
```bash
# FFmpeg兼容性测试
python run_tests.py --test ffmpeg

# 进度反馈测试
python run_tests.py --test progress

# API接口测试
python run_tests.py --test api

# 下载功能测试
python run_tests.py --test download

# 单独运行某个测试文件
python test_demucs.py
python test_full_app.py
python unit/test_download_functionality.py
```

### 3. 前置条件

运行测试前确保：

- ✅ 已安装所有依赖：`pip install -r ../requirements.txt`
- ✅ 测试音频文件存在：`test.mp3`
- ✅ 对于API测试：确保应用服务器运行在 `http://127.0.0.1:8080`

## 📋 测试模块说明

### 核心功能测试

| 测试文件 | 测试内容 | 状态 |
|---------|---------|------|
| `test_demucs.py` | Demucs模型基本功能 | ✅ |
| `test_fixed_separator.py` | 音频分离器修复验证 | ✅ |
| `test_full_app.py` | 完整应用流程测试 | ✅ |

### 兼容性测试

| 测试文件 | 测试内容 | 状态 |
|---------|---------|------|
| `test_ffmpeg_compatibility.py` | FFmpeg库加载和兼容性 | ✅ |
| `test_progress_feedback.py` | 进度回调机制 | ✅ |

### 接口测试

| 测试文件 | 测试内容 | 状态 |
|---------|---------|------|
| `test_api.py` | HTTP API接口完整测试 | ✅ |
| `test_download_functionality.py` | 文件下载功能完整测试 | ✅ |

### MCP协议测试

| 测试文件 | 测试内容 | 状态 |
|---------|---------|------|
| `mcp/client.py` | MCP客户端通信测试 | ✅ |

## 🔧 测试配置

### 环境变量
```bash
# 测试服务器地址
export TEST_SERVER_URL="http://127.0.0.1:8080"

# 测试超时时间
export TEST_TIMEOUT=300
```

### 测试参数

可以在各测试文件中修改以下参数：

- **设备选择**：`device = "cpu"` 或 `device = "cuda"`
- **模型选择**：`model_name = "htdemucs"`
- **音频格式**：支持 mp3, wav, flac 等
- **分离轨道**：`["vocals", "drums", "bass", "other"]`

## 🐛 常见问题

### 1. 内存不足
```python
# 在测试中降低采样率
config = {
    'SAMPLE_RATE': 16000,  # 降低到16kHz
    'CHANNELS': 1          # 使用单声道
}
```

### 2. 测试音频文件缺失
```bash
# 下载测试音频文件
wget -O test.mp3 "https://example.com/test-audio.mp3"
# 或者使用任意短音频文件重命名为test.mp3
```

### 3. API测试失败
```bash
# 确保应用服务器在运行
python ../run.py

# 在另一个终端运行API测试
python test_api.py
```

### 4. GPU/CUDA问题
```python
# 强制使用CPU测试
import torch
if not torch.cuda.is_available():
    device = "cpu"
```

## 📊 测试报告

测试完成后会生成以下输出：

- 🟢 **PASS**: 测试通过
- 🔴 **FAIL**: 测试失败，显示错误信息
- 🟡 **SKIP**: 测试跳过（如缺少依赖）

### 示例输出
```
=== 运行所有测试 ===
test_model_loading (__main__.TestDemucs) ... ok
test_audio_separation (__main__.TestDemucs) ... ok
test_api_models (__main__.TestAPI) ... ok
test_file_upload (__main__.TestAPI) ... ok

----------------------------------------------------------------------
Ran 4 tests in 45.123s

OK
```

## 🔄 持续集成

测试脚本支持CI/CD集成：

```bash
# 在CI环境中运行
python test/run_tests.py --test all
echo "Exit code: $?"
```

## 📝 贡献指南

### 添加新测试

1. 在相应目录创建测试文件
2. 继承 `unittest.TestCase`
3. 添加到 `run_tests.py` 中
4. 更新本README文档

### 测试命名规范

- 测试文件：`test_<模块名>.py`
- 测试类：`Test<功能名>`
- 测试方法：`test_<具体功能>`

### 示例测试结构

```python
import unittest

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        """测试前置条件"""
        pass
    
    def test_basic_functionality(self):
        """测试基本功能"""
        pass
    
    def tearDown(self):
        """测试清理"""
        pass

if __name__ == '__main__':
    unittest.main()
```

## 📞 支持

如果遇到测试问题：

1. 检查是否满足前置条件
2. 查看具体错误信息
3. 参考常见问题部分
4. 查看相关测试文件的注释说明 