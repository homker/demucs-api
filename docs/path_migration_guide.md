# 配置文件路径迁移指南

## 迁移概述

在项目结构整理过程中，我们将配置文件模板移动到了 `config/` 目录，这里详细说明了修改的影响和对应的解决方案。

## 📂 路径变更

### 修改前
```
demucs/
├── .env.example
├── .env.development
├── .env.production
└── .env
```

### 修改后
```
demucs/
├── .env                    # 实际使用的配置文件（保持不变）
└── config/                 # 配置文件模板目录
    ├── .env.example
    ├── .env.development
    └── .env.production
```

## 🔍 影响分析

### ✅ 无需修改的代码
以下代码**无需修改**，因为它们使用动态路径查找：

#### 1. Python应用代码
- `run.py` - 使用 `load_dotenv()` 自动查找根目录的 `.env`
- `app/factory.py` - 同上
- `app/config.py` - 通过 `os.environ.get()` 读取环境变量

#### 2. Docker构建
- `Dockerfile` - 容器内路径不变
- `.dockerignore` - 已更新路径引用

### ⚠️ 已修复的代码
以下文件包含硬编码路径，已经修复：

#### 1. 构建脚本
**文件**: `build/deploy`
- **问题**: 引用 `.env.example` 等配置模板
- **修复**: 更新为 `config/.env.example`
- **改进**: 添加项目根目录自动检测

#### 2. 工具脚本
**文件**: `build/cleanup_files.py`, `build/healthcheck.py`
- **问题**: 在build目录运行时无法找到根目录的 `.env`
- **修复**: 添加项目根目录切换逻辑

## 🔧 修复详情

### 1. build/deploy 脚本修复

```bash
# 修复前
check_env_file() {
    if [ ! -f .env ]; then
        cp .env.example .env  # ❌ 找不到文件
    fi
}

# 修复后
check_env_file() {
    # 获取项目根目录
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$PROJECT_ROOT"
    
    if [ ! -f .env ]; then
        # 从config目录复制配置模板
        if [ -f config/.env.example ]; then
            cp config/.env.example .env  # ✅ 正确路径
        fi
    fi
}
```

### 2. Python脚本路径修复

```python
# 修复前
load_dotenv()  # ❌ 在build/目录下找不到.env

# 修复后
# 获取项目根目录
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# 切换到项目根目录并加载环境变量
os.chdir(PROJECT_ROOT)
load_dotenv()  # ✅ 正确找到根目录的.env
```

## 📋 使用指南

### 开发环境设置

```bash
# 使用开发环境配置
cp config/.env.development .env

# 或者使用快捷脚本
./build.sh help  # 查看可用选项
```

### 生产环境部署

```bash
# 使用生产环境配置
cp config/.env.production .env

# 或通过部署脚本自动选择
./build.sh deploy -e production
```

### 自定义配置

```bash
# 从模板创建自定义配置
cp config/.env.example .env
# 编辑 .env 文件
```

## ✅ 验证迁移

### 测试配置文件加载

```bash
# 测试配置加载
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('BASE_URL:', repr(os.getenv('BASE_URL')))
print('DEBUG:', os.getenv('DEBUG'))
"
```

### 测试构建脚本

```bash
# 测试Docker构建
./build.sh docker

# 测试部署脚本
./build.sh deploy -e development

# 测试清理脚本
./build.sh cleanup --dry-run
```

### 测试健康检查

```bash
# 测试健康检查
./build.sh health
```

## 🔄 回滚方案

如果遇到问题，可以临时回滚：

```bash
# 1. 复制配置文件到根目录（临时）
cp config/.env.example .env.example
cp config/.env.development .env.development
cp config/.env.production .env.production

# 2. 恢复原有的构建脚本逻辑
# (保留备份文件以防需要)
```

## 🎯 最佳实践

### 1. 环境隔离
- 开发环境使用 `config/.env.development`
- 生产环境使用 `config/.env.production`
- 实际部署文件始终为根目录 `.env`

### 2. 脚本运行
- 始终从项目根目录运行 `./build.sh`
- 避免直接运行 `build/` 目录下的脚本

### 3. 配置管理
- 敏感信息不要提交到配置模板
- 使用 `.env` 文件进行本地开发
- 生产环境通过环境变量覆盖配置

## 📞 故障排除

### 问题1: 找不到配置文件

```bash
# 错误信息
ERROR: config template not found

# 解决方案
# 确保从项目根目录运行脚本
cd /path/to/demucs
./build.sh deploy
```

### 问题2: 环境变量加载失败

```bash
# 检查当前工作目录
pwd

# 检查.env文件是否存在
ls -la .env

# 检查配置模板
ls -la config/
```

### 问题3: 构建脚本路径错误

```bash
# 确保使用正确的构建入口
./build.sh docker  # ✅ 正确
cd build && ./docker-build.sh  # ❌ 可能有路径问题
```

这种路径迁移策略确保了：
- 应用代码无需修改
- 配置文件组织更清晰
- 构建脚本能自动处理路径
- 向后兼容性良好 