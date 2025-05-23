# 项目结构说明

## 目录组织

本项目采用清晰的目录结构组织，便于维护和开发：

```
demucs/
├── README.md                    # 项目主要说明文档
├── build.sh                     # 构建快捷脚本
├── .env                         # 主配置文件（不提交到git）
├── requirements.txt             # Python依赖
├── run.py                       # 应用启动入口
├── .gitignore                   # Git忽略规则
├── .gitattributes              # Git属性配置
│
├── app/                         # 应用主代码
│   ├── __init__.py
│   ├── config.py               # 配置管理
│   ├── factory.py              # 应用工厂
│   ├── routes/                 # 路由模块
│   ├── services/               # 业务逻辑
│   ├── templates/              # HTML模板
│   └── static/                 # 静态资源
│
├── build/                       # 构建和部署相关
│   ├── docker-build.sh        # Docker构建脚本
│   ├── Dockerfile              # Docker镜像定义
│   ├── docker-compose.yml      # Docker Compose配置
│   ├── .dockerignore           # Docker忽略规则
│   ├── deploy                  # 部署脚本
│   ├── cleanup_files.py        # 清理脚本
│   └── healthcheck.py          # 健康检查脚本
│
├── config/                      # 配置文件模板
│   ├── .env.example           # 配置模板
│   ├── .env.development       # 开发环境配置
│   └── .env.production        # 生产环境配置
│
├── docs/                        # 项目文档
│   ├── project_structure.md    # 本文件
│   ├── deployment.md           # 部署指南
│   ├── subpath_deployment.md   # 子路径部署指南
│   ├── deployment_update_guide.md # 部署更新指南
│   ├── docker_troubleshooting.md # Docker故障排除
│   ├── env_configuration_guide.md # 环境配置指南
│   └── test_subpath_deployment.py # 部署测试脚本
│
├── test/                        # 测试文件
│   └── ...                     # 测试相关文件
│
├── logs/                        # 日志文件
│   └── app.log                 # 应用日志
│
├── uploads/                     # 用户上传文件
├── outputs/                     # 处理结果文件
└── models/                      # AI模型文件（运行时创建）
```

## 目录说明

### 核心目录

#### `/app` - 应用代码
包含Flask应用的所有核心代码：
- `config.py` - 配置管理和环境变量处理
- `factory.py` - 应用工厂模式，创建和配置Flask实例
- `routes/` - 路由定义（API路由、MCP路由等）
- `services/` - 业务逻辑（音频处理、文件管理等）
- `templates/` - Jinja2 HTML模板
- `static/` - CSS、JavaScript、图片等静态资源

#### `/build` - 构建和部署
集中管理所有构建相关文件：
- **Docker相关**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **构建脚本**: `docker-build.sh` - Docker镜像构建
- **部署脚本**: `deploy` - 自动化部署
- **维护脚本**: `cleanup_files.py`, `healthcheck.py`

#### `/config` - 配置模板
环境配置文件模板，便于不同环境部署：
- `.env.example` - 配置模板和文档
- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

#### `/docs` - 项目文档
集中管理所有项目文档：
- **部署文档**: 部署指南、故障排除
- **配置文档**: 环境配置、子路径部署
- **测试文档**: 测试脚本和验证工具

### 工作目录

#### `/uploads` - 上传文件
用户上传的音频文件临时存储目录。

#### `/outputs` - 输出文件  
音频分离处理后的结果文件存储目录。

#### `/logs` - 日志文件
应用运行日志和错误日志存储目录。

#### `/models` - AI模型
Demucs AI模型文件，首次运行时自动下载。

## 文件组织原则

### 1. 关注点分离
- **代码** (`/app`) - 核心应用逻辑
- **构建** (`/build`) - 构建和部署相关
- **配置** (`/config`) - 环境配置模板
- **文档** (`/docs`) - 项目文档和指南

### 2. 环境隔离
- 开发环境使用 `config/.env.development`
- 生产环境使用 `config/.env.production`
- 实际部署使用根目录 `.env` 文件

### 3. 构建便捷性
- 根目录保持简洁，只有必要文件
- 使用 `build.sh` 作为所有构建操作的统一入口
- 构建脚本自动处理路径和依赖关系

## 快捷操作

### 构建操作
```bash
# 构建Docker镜像
./build.sh docker

# 运行部署
./build.sh deploy

# 清理临时文件
./build.sh cleanup

# 健康检查
./build.sh health
```

### 配置管理
```bash
# 开发环境
cp config/.env.development .env

# 生产环境
cp config/.env.production .env

# 自定义配置
cp config/.env.example .env
# 编辑 .env 文件
```

### 文档查看
- 主要文档：`README.md`
- 部署指南：`docs/deployment.md`
- 配置指南：`docs/env_configuration_guide.md`
- 故障排除：`docs/docker_troubleshooting.md`

## 最佳实践

### 1. 开发流程
1. 从配置模板创建 `.env` 文件
2. 在 `/app` 目录下进行代码开发
3. 使用 `./build.sh docker` 构建测试
4. 查看 `/docs` 目录了解部署和配置

### 2. 部署流程
1. 选择合适的配置模板 (`config/.env.production`)
2. 使用 `./build.sh deploy` 自动化部署
3. 参考 `docs/deployment.md` 进行配置调整

### 3. 维护流程
1. 使用 `./build.sh cleanup` 定期清理
2. 使用 `./build.sh health` 检查应用状态
3. 查看 `/logs` 目录监控应用运行

## 版本控制

### Git忽略策略
- 忽略实际的 `.env` 文件（包含敏感信息）
- 保留配置模板文件 (`config/`)
- 忽略运行时生成的文件 (`uploads/`, `outputs/`, `logs/`)
- 忽略构建产物但保留构建脚本

### 文件权限
- 构建脚本：755 (可执行)
- 配置文件：644 (可读写)
- 敏感配置：600 (仅所有者可读写)

这种组织结构确保了项目的可维护性、可扩展性和部署便捷性。 