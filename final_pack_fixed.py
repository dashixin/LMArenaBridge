#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复版打包脚本 - 解决重复启动 GUI 的问题
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
    """使用修复后的PyInstaller命令"""
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
        # 隐藏导入
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "_cffi_backend",
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "websockets",
        "--hidden-import", "httpx",
        "--hidden-import", "starlette",
        # 添加Python脚本作为数据文件
        "--add-data", "api_server.py;.",
        "--add-data", "id_updater.py;.",
        "--add-data", "model_updater.py;.",
        "--add-data", "auth_system.py;.",
        "--add-data", "auth_keygen.py;.",
        # 添加模块目录
        "--add-data", "modules;modules",
        # 主入口文件
        "lmarena_manager.py"
    ]
    
    # Windows 特定的分隔符
    if sys.platform == "win32":
        # 替换分号为Windows的分隔符
        cmd = [arg.replace(";", ";") if "--add-data" not in arg else arg for arg in cmd]
    
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
        "requirements.txt",  # 可能需要用于参考
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
        "file_bed_server",
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
start "" "LMArenaBridge.exe"
'''
    
    dist_dir = Path("dist/LMArenaBridge")
    if dist_dir.exists():
        with open(dist_dir / "启动LMArenaBridge.bat", 'w', encoding='gbk') as f:
            f.write(batch_content)
        print("✓ 已创建启动批处理文件")

def create_readme():
    """创建说明文件"""
    readme_content = '''# LMArenaBridge 使用说明

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

## 注意事项
- 如果防火墙提示，请选择"允许访问"
- 确保端口 5102 和 5103 未被占用
- 日志文件会显示在界面中，可以导出保存

## 故障排除
- 如果无法启动，请检查是否有其他程序占用端口
- 可以使用"Kill"按钮强制终止占用端口的进程
- 查看日志了解详细错误信息
'''
    
    dist_dir = Path("dist/LMArenaBridge")
    if dist_dir.exists():
        with open(dist_dir / "使用说明.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✓ 已创建使用说明")

def main():
    """主函数"""
    print("=== LMArenaBridge 修复版打包脚本 ===\n")
    
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
    
    # 6. 完成
    print("\n" + "="*50)
    print("✓ 打包完成！")
    print("="*50)
    print(f"\n输出目录: {os.path.abspath('dist/LMArenaBridge')}")
    print("\n包含的文件:")
    print("- LMArenaBridge.exe (主程序)")
    print("- 启动LMArenaBridge.bat (启动脚本)")
    print("- 使用说明.txt (使用指南)")
    print("- 所有配置文件")
    print("- 所有必要的目录和文件")
    print("\n重要提示:")
    print("- 此版本已修复重复启动GUI的问题")
    print("- API服务器将在程序内部线程中运行")
    print("- 如需进一步优化，请参考'打包问题分析与解决方案.md'")

if __name__ == "__main__":
    main()
