#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终打包脚本 - 使用已验证的命令并复制配置文件
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
    """使用已验证的PyInstaller命令"""
    print("\n开始打包...")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "LMArenaBridge",
        "--collect-all", "cryptography",
        "--collect-all", "cffi",
        "--hidden-import", "cryptography.fernet",
        "--hidden-import", "_cffi_backend",
        "lmarena_manager.py"
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
    ]
    
    # 复制单个文件
    for file in files_to_copy:
        if os.path.exists(file):
            try:
                shutil.copy2(file, dist_dir / file)
                print(f"✓ 已复制: {file}")
            except Exception as e:
                print(f"✗ 复制 {file} 失败: {e}")
    return True

def create_batch_file():
    """创建启动批处理文件"""
    batch_content = '''@echo off
cd /d "%~dp0"
start "" "LMArenaBridge.exe"
'''
    
    dist_dir = Path("dist/LMArenaBridge")
    if dist_dir.exists():
        with open(dist_dir / "启动LMArenaBridge.bat", 'w', encoding='gbk') as f:
            f.write(batch_content)
        print("✓ 已创建启动批处理文件")

def main():
    """主函数"""
    print("=== LMArenaBridge 最终打包脚本 ===\n")
    
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
    
    # 5. 完成
    print("\n" + "="*50)
    print("✓ 打包完成！")
    print("="*50)
    print(f"\n输出目录: {os.path.abspath('dist/LMArenaBridge')}")
    print("\n包含的文件:")
    print("- LMArenaBridge.exe (主程序)")
    print("- 启动LMArenaBridge.bat (启动脚本)")
    print("- 所有配置文件 (config.jsonc, models.json等)")
    print("- 所有必要的目录和文件")
    print("\n使用方法:")
    print("1. 将整个 dist/LMArenaBridge 文件夹复制到目标电脑")
    print("2. 双击 启动LMArenaBridge.bat 或 LMArenaBridge.exe 运行")
    print("3. 配置文件可以随时修改")

if __name__ == "__main__":
    main()
