# GitHub Actions 自动构建 Mac 版本使用指南

## 项目信息
- **GitHub 仓库**: https://github.com/dashixin/LMArenaBridge
- **工作流文件**: `.github/workflows/build-mac.yml`

## 自动构建触发方式

### 1. 推送代码时自动触发
- 推送到 `master` 或 `main` 分支时自动触发构建
- 创建版本标签（如 `v1.0.0`）时自动触发构建并创建 Release

### 2. 手动触发构建
1. 访问 [Actions 页面](https://github.com/dashixin/LMArenaBridge/actions)
2. 点击左侧的 "Build macOS Application"
3. 点击右侧的 "Run workflow" 按钮
4. 选择分支和构建类型
5. 点击绿色的 "Run workflow" 按钮

## 查看构建状态

### 方法一：通过 GitHub 网页
1. 访问 https://github.com/dashixin/LMArenaBridge/actions
2. 查看工作流运行列表
3. 点击具体的运行记录查看详细日志

### 方法二：在 README 中添加状态徽章
在 `README.md` 中添加以下代码：
```markdown
![Build Status](https://github.com/dashixin/LMArenaBridge/workflows/Build%20macOS%20Application/badge.svg)
```

## 下载构建产物

### 从工作流运行页面下载
1. 进入具体的工作流运行页面
2. 滚动到页面底部的 "Artifacts" 部分
3. 点击 `LMArenaBridge-macOS-{commit-sha}` 下载

### 从 Release 页面下载（仅限版本发布）
1. 访问 https://github.com/dashixin/LMArenaBridge/releases
2. 下载最新版本的 `LMArenaBridge-macOS.zip`

## 创建版本发布

1. 在本地创建并推送标签：
```bash
# 创建标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到 GitHub
git push origin v1.0.0
```

2. GitHub Actions 会自动：
   - 构建 Mac 应用
   - 创建 Release
   - 上传构建文件到 Release

## 故障排查

### 查看构建日志
1. 进入失败的工作流运行
2. 点击失败的步骤查看详细错误信息

### 常见问题
1. **依赖安装失败**
   - 检查 `requirements.txt` 是否正确
   - 确认所有依赖都支持 macOS

2. **打包失败**
   - 检查 `mac-pack.py` 脚本
   - 确认所有必要文件都已提交

3. **上传失败**
   - 确认使用的是 `actions/upload-artifact@v4`
   - 检查文件路径是否正确

## 工作流配置说明

当前工作流配置：
- **运行环境**: macOS 最新版本
- **Python 版本**: 3.9
- **构建工具**: PyInstaller
- **产物保留时间**: 30 天
- **自动创建 Release**: 仅在推送标签时

## 后续优化建议

1. **添加测试步骤**
   - 在打包前运行单元测试
   - 验证打包后的应用能否正常启动

2. **多版本支持**
   - 支持不同的 macOS 版本
   - 支持 Intel 和 Apple Silicon 架构

3. **代码签名**
   - 添加 Apple 开发者证书签名
   - 进行公证（Notarization）

4. **缓存优化**
   - 缓存 Python 依赖
   - 缓存构建中间文件

## 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [PyInstaller 文档](https://pyinstaller.org/en/stable/)
- [actions/upload-artifact](https://github.com/actions/upload-artifact)
- [softprops/action-gh-release](https://github.com/softprops/action-gh-release)
