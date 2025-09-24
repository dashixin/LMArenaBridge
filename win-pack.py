#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案二打包脚本 - 使用统一入口点
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_old_files():
    """清理旧的打包文件"""
    print("清理旧文件...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # 删除所有.spec文件
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
    print("✓ 清理完成")

def run_pyinstaller():
    """使用PyInstaller打包统一入口文件"""
    print("\n开始打包...")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "LMArenaBridge",
        # 收集必要的包
        "--collect-all", "cryptography",
        "--collect-all", "cffi",
        "--collect-all", "fastapi",
        "--collect-all", "uvicorn",
        "--collect-all", "websockets",
        "--collect-all", "httpx",
        "--collect-all", "starlette",
        # 隐藏导入
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "_cffi_backend",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "websockets",
        "--hidden-import", "httpx",
        "--hidden-import", "starlette",
        "--hidden-import", "lmarena_manager",
        "--hidden-import", "api_server",
        "--hidden-import", "id_updater",
        "--hidden-import", "model_updater",
        "--hidden-import", "auth_system",
        "--hidden-import", "auth_keygen",
        "--hidden-import", "main",  # 添加main模块
        # 添加所有Python文件作为隐藏导入，确保它们被包含
        "--hidden-import", "modules.file_uploader",
        "--hidden-import", "modules.update_script",
        # 主入口文件
        "encoding_fix.py"  # 使用编码修复脚本作为入口
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✓ 打包成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False

def copy_config_files():
    """复制配置文件和其他必要文件到输出目录"""
    print("\n复制配置文件...")
    
    dist_dir = Path("dist/LMArenaBridge")
    if not dist_dir.exists():
        print("✗ 输出目录不存在")
        return False
    
    # 需要复制的文件列表
    files_to_copy = [
        "config.jsonc",
        "models.json",
        "model_endpoint_map.json",
        "available_models.json",
        "requirements.txt",
    ]
    
    # 复制单个文件
    for file in files_to_copy:
        if os.path.exists(file):
            try:
                shutil.copy2(file, dist_dir / file)
                print(f"✓ 已复制: {file}")
            except Exception as e:
                print(f"✗ 复制 {file} 失败: {e}")
    
    # 复制目录
    dirs_to_copy = [
        "TampermonkeyScript"
    ]
    
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            try:
                shutil.copytree(dir_name, dist_dir / dir_name)
                print(f"✓ 已复制目录: {dir_name}")
            except Exception as e:
                print(f"✗ 复制目录 {dir_name} 失败: {e}")
    
    return True

def create_batch_file():
    """创建启动批处理文件"""
    batch_content = '''@echo off
cd /d "%~dp0"
echo LMArenaBridge 启动中...
echo.
echo 注意：如果出现防火墙提示，请选择"允许访问"
echo.
echo 正在启动主程序...
start "" "LMArenaBridge.exe"
'''
    
    dist_dir = Path("dist/LMArenaBridge")
    if dist_dir.exists():
        with open(dist_dir / "启动LMArenaBridge.bat", 'w', encoding='gbk') as f:
            f.write(batch_content)
        print("✓ 已创建启动批处理文件")

def create_readme():
    """创建说明文件"""
    readme_content = '''# LMArenaBridge 使用说明（方案二版本）

## 运行要求
- Windows 10/11 系统
- 需要安装油猴脚本（TampermonkeyScript 目录中）
- 需要能访问 LMArena 网站

## 使用步骤
1. 双击"启动LMArenaBridge.bat"运行程序
2. 首次运行需要输入授权码
3. 启动后会显示管理界面
4. 在"服务管理"标签页点击"启动"按钮启动API服务器
5. 配置文件可以直接编辑 config.jsonc 和 models.json

## 技术说明
本版本使用统一入口点方式打包，所有功能模块都集成在一个exe文件中。
通过命令行参数来调用不同的模块功能。

## 注意事项
- 如果防火墙提示，请选择"允许访问"
- 确保端口 5102 和 5103 未被占用
- 日志文件会显示在界面中，可以导出保存

## 故障排除
- 如果无法启动，请检查是否有其他程序占用端口
- 可以使用"Kill"按钮强制终止占用端口的进程
- 查看日志了解详细错误信息

## 方案二特点
- 使用统一入口文件 (main.py)
- 通过参数调用不同模块
- 解决了打包后重复启动GUI的问题
'''
    
    dist_dir = Path("dist/LMArenaBridge")
    if dist_dir.exists():
        with open(dist_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✓ 已创建使用说明")

def create_implementation_guide():
    """创建实施指南"""
    guide_content = '''# 方案二实施指南

## 修改步骤

1. **使用新的 main.py 作为入口文件**
   - main.py 已创建，它会根据命令行参数调用不同的模块

2. **修改 lmarena_manager.py**
   - 找到 `start_api_server` 方法
   - 将 `[sys.executable, "api_server.py"]` 改为 `[sys.executable, "api_server"]`
   
   - 找到 `_run_id_updater_process` 方法
   - 将 `[sys.executable, "id_updater.py"]` 改为 `[sys.executable, "id_updater"]`

3. **运行打包脚本**
   ```
   python final_pack_v2.py
   ```

4. **测试**
   - 运行生成的 LMArenaBridge.exe
   - 测试启动API服务器功能
   - 测试更新会话ID功能

## 代码修改示例

请参考 lmarena_manager_v2_patch.py 文件中的修改示例。

## 注意事项
- 确保所有模块都能被正确导入
- 打包时会将所有依赖都包含进去
- 如果遇到导入错误，可能需要添加更多的 --hidden-import
'''
    
    with open("方案二实施指南.txt", 'w', encoding='utf-8') as f:
        f.write(guide_content)
    print("✓ 已创建实施指南")

def main():
    """主函数"""
    print("=== LMArenaBridge 方案二打包脚本 ===\n")
    print("使用统一入口点方式解决打包问题\n")
    
    # 检查 main.py 是否存在
    if not os.path.exists("main.py"):
        print("✗ 错误：找不到 main.py 文件")
        print("请确保 main.py 文件存在")
        return
    
    # 1. 清理旧文件
    clean_old_files()
    
    # 2. 运行PyInstaller
    if not run_pyinstaller():
        print("\n打包失败，请检查错误信息")
        return
    
    # 3. 复制配置文件
    if not copy_config_files():
        print("\n复制文件失败")
        return
    
    # 4. 创建启动批处理
    create_batch_file()
    
    # 5. 创建说明文件
    create_readme()
    
    # 6. 创建实施指南
    create_implementation_guide()
    
    # 7. 完成
    print("\n" + "="*50)
    print("✓ 方案二打包完成！")
    print("="*50)
    print(f"\n输出目录: {os.path.abspath('dist/LMArenaBridge')}")
    print("\n重要提示:")
    print("1. 请先按照 '方案二实施指南.txt' 修改 lmarena_manager.py")
    print("2. 修改完成后再运行打包后的程序")
    print("3. 这个方案通过统一入口点解决了重复启动GUI的问题")
    print("\n下一步:")
    print("1. 查看 lmarena_manager_v2_patch.py 了解需要修改的代码")
    print("2. 修改 lmarena_manager.py 中的相关方法")
    print("3. 测试打包后的程序")

if __name__ == "__main__":
    main()
