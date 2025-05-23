# 项目文档导航

本目录包含Demucs音频分离项目的所有技术文档。

## 📚 文档列表

### 核心文档

- **[项目结构说明](project_structure.md)** - 详细的项目目录组织和文件说明
- **[部署指南](deployment.md)** - 完整的部署流程和配置说明
- **[环境配置指南](env_configuration_guide.md)** - 环境变量和配置文件详细说明

### 部署专题

- **[子路径部署指南](subpath_deployment.md)** - 子路径（如`/demucs`）部署的专门指南
- **[部署更新指南](deployment_update_guide.md)** - 现有部署的更新和问题修复指南
- **[Docker故障排除](docker_troubleshooting.md)** - Docker构建和运行常见问题解决

### 故障排除

- **[静态文件路径问题](static_files_path_guide.md)** - 解决静态文件404错误和路径配置问题
- **[路径迁移指南](path_migration_guide.md)** - 配置文件路径变更的影响和解决方案

### 测试工具

- **[子路径部署测试](test_subpath_deployment.py)** - 自动化测试脚本，验证子路径部署功能

## 🚀 快速入门

如果你是第一次使用这个项目：

1. 📖 先阅读 [项目结构说明](project_structure.md) 了解项目组织
2. ⚙️ 参考 [环境配置指南](env_configuration_guide.md) 设置环境
3. 🚀 按照 [部署指南](deployment.md) 部署应用

## 🔧 常见场景

### 开发环境搭建
```bash
# 1. 配置开发环境（根路径访问）
./config_switch.sh local

# 2. 启动应用
python run.py

# 3. 访问应用
open http://127.0.0.1:8080/
```

### 生产环境部署
```bash
# 1. 配置生产环境（子路径访问）
./config_switch.sh prod

# 2. 构建和部署
./build.sh docker
./build.sh deploy
```

### 子路径部署（如 /demucs）
```bash
# 1. 使用子路径配置
./config_switch.sh subpath

# 2. 测试配置
python docs/test_subpath_deployment.py

# 3. 部署
./build.sh deploy
```

### 故障排除
- 构建问题 → [Docker故障排除](docker_troubleshooting.md)
- 配置问题 → [环境配置指南](env_configuration_guide.md)
- 路径问题 → [子路径部署指南](subpath_deployment.md)
- 静态文件404 → [静态文件路径问题](static_files_path_guide.md)

## 📝 文档维护

### 添加新文档
1. 在对应的主题目录下创建文档
2. 更新本文档的导航链接
3. 在主README.md中添加相关链接

### 文档编写规范
- 使用中文编写
- 包含实际的代码示例
- 提供故障排除步骤
- 保持与项目结构同步更新

## 🔗 相关链接

- **主项目README**: [../README.md](../README.md)
- **构建脚本**: [../build.sh](../build.sh)
- **配置切换脚本**: [../config_switch.sh](../config_switch.sh)
- **配置模板**: [../config/](../config/)
- **构建工具**: [../build/](../build/)

## 📞 支持

如果在使用过程中遇到问题：

1. 查看相关的故障排除文档
2. 运行测试脚本验证配置
3. 检查项目日志文件
4. 参考[项目结构说明](project_structure.md)了解文件组织 