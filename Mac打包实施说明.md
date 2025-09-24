# LMArenaBridge Mac版打包实施说明

## 概述

本文档说明如何将 LMArenaBridge 项目打包成 macOS 可执行文件，同时确保不影响 Windows 版本的正常运行。

## 实施方案特点

1. **零影响**：Windows 版本功能完全不受影响
2. **跨平台兼容**：使用条件判断和平台适配层
3. **统一代码库**：一套代码支持多平台
4. **易于维护**：平台相关代码分离

## 已完成的修改

### 1. 创建的新文件

- **platform_utils.py** - 平台工具函数，处理跨平台差异
- **auth_system_mac.py** - Mac版授权系统，使用macOS特定的硬件信息
- **mac-pack.py** - Mac专用打包脚本

### 2. 修改的现有文件

- **auth_system.py** - 添加了平台判断，macOS时使用专门的机器码生成方法
- **lmarena_manager.py** - 使用平台工具函数替代了硬编码的Windows特定代码

### 3. 主要改动点

#### 授权系统
- Windows：继续使用原有的MAC地址+主机名方式
- macOS：使用序列号、硬件UUID、型号等Mac特定信息

#### 进程管理
- Windows：使用 `taskkill` 命令
- macOS：使用 `lsof` 和 `kill` 命令

#### 环境设置
- 统一使用 `platform_utils` 中的函数处理UTF-8编码和进程启动参数

## 使用方法

### 在 Windows 上打包

```bash
# 使用原有的打包脚本
python win-pack.py
```

### 在 macOS 上打包

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller

# 2. 运行Mac打包脚本
python mac-pack.py
```

## Mac打包输出

打包完成后，`dist` 目录将包含：

- **LMArenaBridge.app** - 主应用程序
- **启动LMArenaBridge.command** - 启动脚本
- **使用说明.txt** - 用户使用说明
- **LMArenaBridge-macOS.dmg** - DMG安装包（如果创建成功）

## 注意事项

### 1. 授权系统

- Mac版本使用不同的机器码生成方式
- 授权码生成算法保持一致
- Windows和Mac的授权码不能通用（因为机器码不同）

### 2. 测试建议

- 在Windows上测试确保原有功能正常
- 在Mac上测试所有功能，特别是：
  - 授权验证流程
  - API服务器启动/停止
  - 进程终止功能
  - 会话ID更新

### 3. 可能的问题

- **权限问题**：Mac上可能需要授予应用访问权限
- **安全提示**：首次运行时需要在系统偏好设置中允许
- **依赖问题**：确保所有Python依赖都已正确安装

## 后续优化建议

1. **图标设计**：为Mac版本添加专门的应用图标
2. **代码签名**：考虑对Mac应用进行代码签名
3. **自动更新**：实现跨平台的自动更新机制
4. **统一授权**：考虑实现跨平台的授权系统

## 技术细节

### 平台检测

```python
import sys

if sys.platform == "darwin":  # macOS
    # Mac特定代码
elif sys.platform == "win32":  # Windows
    # Windows特定代码
```

### 关键函数

- `get_platform()` - 获取当前平台
- `kill_process_by_port()` - 跨平台终止进程
- `ensure_utf8_environment()` - 确保UTF-8环境
- `get_startup_info()` - 获取进程启动信息

## 总结

通过创建平台适配层和使用条件判断，我们成功实现了：

1. 保持Windows版本完全不受影响
2. 添加完整的macOS支持
3. 维护统一的代码库
4. 提供良好的用户体验

这种方案确保了项目的可维护性和可扩展性，未来可以轻松添加Linux支持。
