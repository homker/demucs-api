# 音频分离应用测试文档

本目录包含Demucs音频分离应用的测试代码。测试涵盖了FFmpeg兼容性、进度反馈机制和API接口功能。

## 测试组件

测试组件分为以下几个模块：

1. **FFmpeg兼容性测试** (`test_ffmpeg_compatibility.py`)
   - 测试FFmpeg库加载
   - 测试符号链接创建
   - 测试文件路径解析

2. **进度反馈测试** (`test_progress_feedback.py`)
   - 测试进度回调功能
   - 测试进度值更新机制
   - 测试模型应用过程的进度报告

3. **API接口测试** (`test_api.py`)
   - 测试所有HTTP API接口
   - 测试文件上传和处理
   - 测试进度监控(SSE)
   - 测试文件下载
   - 测试错误处理

## 运行测试

可以使用`run_tests.py`脚本运行测试。此脚本支持选择运行特定类型的测试或全部测试。

### 基本用法

```bash
# 运行所有测试
python run_tests.py

# 运行FFmpeg兼容性测试
python run_tests.py --test ffmpeg

# 运行进度反馈测试
python run_tests.py --test progress

# 运行API接口测试
python run_tests.py --test api
```

### 运行API测试的前提条件

运行API测试前，确保：

1. 应用服务器正在运行(`python run.py`)
2. 测试目录中存在测试音频文件`test.mp3`
3. 服务器运行在默认端口5000上

### 测试文件

- `test.mp3`：用于测试的音频文件
- `run_tests.py`：测试运行器
- `test_ffmpeg_compatibility.py`：FFmpeg兼容性测试
- `test_progress_feedback.py`：进度反馈测试
- `test_api.py`：API接口测试

## 注意事项

1. API测试会创建实际的处理任务并生成文件，测试完成后会自动清理
2. 确保有足够的磁盘空间用于测试
3. 某些测试可能需要一定时间完成，特别是涉及音频处理的测试

## 测试文件

- **test_demucs.py**: 基本的Demucs功能测试，展示了模型加载和音频处理流程。
- **test_fixed_separator.py**: 展示了针对维度不匹配问题的修复方法，特别是处理"not enough values to unpack (expected 3, got 2)"错误。
- **test_full_app.py**: 全面的应用测试，测试所有主要接口和功能，包括模型、服务、文件管理和API端点。
- **run_tests.py**: 用于选择性地运行特定测试模块的脚本。

## 使用方法

1. 确保安装了所有必要依赖：
   ```
   pip install -r requirements.txt
   ```

2. 确保在test目录下有一个名为`test.mp3`的测试音频文件。

3. 运行基本测试：
   ```
   python test/test_demucs.py      # 运行基本测试
   python test/test_fixed_separator.py  # 运行修复方法测试
   ```

4. 运行全面测试：
   ```
   python test/test_full_app.py    # 运行全部测试
   ```

5. 选择性运行特定测试：
   ```
   python test/run_tests.py --test model    # 只运行模型功能测试
   python test/run_tests.py --test service  # 只运行音频分离服务测试
   python test/run_tests.py --test file     # 只运行文件管理测试
   python test/run_tests.py --test api      # 只运行API端点测试
   python test/run_tests.py --test all      # 运行全部测试(默认)
   ```

## 修复的问题

1. **维度不匹配问题**：
   - 问题：demucs的apply_model函数期望输入张量形状为[batch, channels, length]，但有时接收到[channels, length]形状的输入
   - 解决方法：使用torch.unsqueeze(0)添加批处理维度

2. **参数命名问题**：
   - 问题：save_audio函数的参数名为'samplerate'而非'sample_rate'
   - 解决方法：更新函数调用，使用正确的参数名

## 测试模块说明

- **模型测试**: 测试Demucs模型的基本功能，包括模型加载、音频加载和处理。
- **服务测试**: 测试AudioSeparator服务，包括服务初始化和音频分离功能。
- **文件管理测试**: 测试FileManager服务，包括目录创建、文件上传处理和ZIP文件创建。
- **API测试**: 测试应用的API端点，包括获取模型列表、处理音频和下载结果。

## 输出说明

测试脚本将分离的音频轨道保存在`test/output/`目录中。

## 测试结果

| 测试模块 | 状态 | 说明 |
|---------|------|------|
| 模型测试 | ✅ 通过 | 所有测试成功完成，模型可以正常加载并处理音频 |
| 服务测试 | ✅ 通过 | AudioSeparator服务可以正常初始化和分离音频 |
| 文件管理测试 | ✅ 通过 | 文件管理功能工作正常，包括目录创建、文件上传和ZIP创建 |
| API测试 | ⚠️ 部分通过 | 获取模型列表API测试通过，但上传文件API测试需要在实际环境中验证 |

## 调试提示

如果在运行测试过程中遇到问题：

1. **路径问题**：确保在正确的目录下运行命令。测试脚本使用相对路径查找资源。

2. **音频文件**：确保test目录下存在名为`test.mp3`的测试音频文件。

3. **依赖问题**：确保安装了所有必要的依赖：
   ```
   pip install torch torchaudio demucs flask werkzeug
   ```

4. **内存问题**：如果在处理大型音频文件时遇到内存错误，可以修改测试参数降低批处理大小或减少样本率。

5. **GPU支持**：默认测试使用CPU。如果要使用GPU，需要修改测试脚本中的`device`参数为"cuda"。

## API测试注意事项

API测试中的文件上传测试目前被注释掉，因为在测试环境中正确模拟文件上传比较复杂。如果需要完整测试API，可能需要：

1. 在实际运行的应用环境中进行测试，而不是使用测试客户端
2. 使用专用的测试工具如Postman或curl发送真实的multipart/form-data请求
3. 修改API代码以更好地支持测试环境 