#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac版打包脚本
使用PyInstaller将LMArenaBridge打包成macOS应用
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def is_ci_environment():
    """检测是否在 CI 环境中运行"""
    return os.environ.get('CI') == 'true' or os.environ.get('GITHUB_ACTIONS') == 'true'


def check_environment():
    """检查环境"""
    print("检查环境...")
    
    # 检查是否在macOS上运行
    if sys.platform != "darwin":
        print("❌ 此脚本只能在macOS上运行")
        return False
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False
    
    # 检查必要文件
    required_files = ["main.py", "lmarena_manager.py", "auth_system.py", "auth_system_mac.py", "platform_utils.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return False
    
    print("✓ 环境检查通过")
    return True


def clean_old_files():
    """清理旧的打包文件"""
    print("\n清理旧文件...")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # 删除所有.spec文件
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
    print("✓ 清理完成")


def create_spec_file():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.jsonc', '.'),
        ('models.json', '.'),
        ('model_endpoint_map.json', '.'),
        ('available_models.json', '.'),
        ('TampermonkeyScript', 'TampermonkeyScript'),
    ],
    hiddenimports=[
        'cryptography',
        'cryptography.fernet',
        '_cffi_backend',
        'fastapi',
        'uvicorn',
        'websockets',
        'httpx',
        'starlette',
        'lmarena_manager',
        'api_server',
        'id_updater',
        'model_updater',
        'auth_system',
        'auth_system_mac',
        'auth_keygen',
        'platform_utils',
        'modules.file_uploader',
        'modules.update_script',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LMArenaBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch='universal2',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LMArenaBridge',
)

app = BUNDLE(
    coll,
    name='LMArenaBridge.app',
    icon=None,
    bundle_identifier='com.lmarena.bridge',
    info_plist={
        'CFBundleName': 'LMArenaBridge',
        'CFBundleDisplayName': 'LMArenaBridge Manager',
        'CFBundleGetInfoString': "LMArenaBridge Manager for macOS",
        'CFBundleIdentifier': "com.lmarena.bridge",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0',
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
    },
)
'''
    
    with open('LMArenaBridge.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ 创建spec文件成功")


def run_pyinstaller():
    """使用PyInstaller打包"""
    print("\n开始打包...")
    
    # 检查 TampermonkeyScript 目录是否存在
    if not os.path.exists('TampermonkeyScript'):
        print("❌ TampermonkeyScript 目录不存在")
        return False
    else:
        print("✓ TampermonkeyScript 目录存在")
        print("  目录内容:")
        for item in os.listdir('TampermonkeyScript'):
            print(f"    - {item}")
    
    try:
        # 使用spec文件打包
        subprocess.check_call(['pyinstaller', '--clean', '--noconfirm', 'LMArenaBridge.spec'])
        print("✓ 打包成功")
        
        # 检查生成的文件
        if os.path.exists("dist/LMArenaBridge.app"):
            print("✓ .app 文件已生成")
            
            # 检查 TampermonkeyScript 是否被包含
            possible_paths = [
                "dist/LMArenaBridge.app/Contents/Resources/TampermonkeyScript",
                "dist/LMArenaBridge.app/Contents/MacOS/TampermonkeyScript",
                "dist/LMArenaBridge.app/Contents/Frameworks/TampermonkeyScript"
            ]
            
            found = False
            for path in possible_paths:
                if os.path.exists(path):
                    print(f"✓ TampermonkeyScript 目录在: {path}")
                    found = True
                    break
            
            if not found:
                print("⚠️ TampermonkeyScript 目录未在 .app 包中找到")
        else:
            print("❌ .app 文件未生成")
            # 检查是否生成了目录而非 .app
            if os.path.exists("dist/LMArenaBridge"):
                print("⚠️ 发现 LMArenaBridge 目录，可能需要手动转换为 .app")
            return False
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        return False


def create_dmg():
    """创建DMG安装包（可选）"""
    print("\n创建DMG安装包...")
    
    if not os.path.exists("dist/LMArenaBridge.app"):
        print("❌ 找不到打包后的应用")
        return False
    
    try:
        # 创建临时目录
        dmg_temp = "dist/dmg_temp"
        if os.path.exists(dmg_temp):
            shutil.rmtree(dmg_temp)
        os.makedirs(dmg_temp)
        
        # 复制应用到临时目录
        shutil.copytree("dist/LMArenaBridge.app", f"{dmg_temp}/LMArenaBridge.app")
        
        # 创建Applications链接
        os.symlink("/Applications", f"{dmg_temp}/Applications")
        
        # 创建DMG
        dmg_name = "LMArenaBridge-macOS.dmg"
        subprocess.check_call([
            'hdiutil', 'create', '-volname', 'LMArenaBridge',
            '-srcfolder', dmg_temp, '-ov', '-format', 'UDZO',
            f"dist/{dmg_name}"
        ])
        
        # 清理临时目录
        shutil.rmtree(dmg_temp)
        
        print(f"✓ DMG创建成功: dist/{dmg_name}")
        return True
        
    except Exception as e:
        print(f"❌ 创建DMG失败: {e}")
        print("提示：您可以手动将.app文件拖到Applications文件夹安装")
        return False


def create_launch_script():
    """创建启动脚本"""
    script_content = '''#!/bin/bash
# LMArenaBridge 启动脚本

echo "LMArenaBridge 启动中..."
echo ""
echo "注意事项："
echo "1. 首次运行可能需要在'系统偏好设置 > 安全性与隐私'中允许运行"
echo "2. 确保已安装油猴脚本（TampermonkeyScript目录中）"
echo "3. 需要能访问LMArena网站"
echo ""

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 启动应用
open "$DIR/LMArenaBridge.app"
'''
    
    script_path = "dist/启动LMArenaBridge.command"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    # 添加执行权限
    os.chmod(script_path, 0o755)
    print("✓ 创建启动脚本成功")


def create_readme():
    """创建说明文件"""
    readme_content = '''# LMArenaBridge macOS版使用说明

## 系统要求
- 支持的 macOS 版本：
  - macOS Monterey (12.0) 或更高版本
  - macOS Ventura (13.0)
  - macOS Sonoma (14.0)
  - macOS Sequoia (15.0)
- 支持 Intel 和 Apple Silicon (M1/M2/M3) 处理器
- 需要安装油猴脚本（TampermonkeyScript目录中）

## 安装方法

### 方法一：使用DMG安装包
1. 双击 LMArenaBridge-macOS.dmg
2. 将 LMArenaBridge.app 拖到 Applications 文件夹
3. 在 Applications 中找到并运行 LMArenaBridge

### 方法二：直接运行
1. 双击 "启动LMArenaBridge.command"
2. 或者直接双击 LMArenaBridge.app

## 首次运行

1. **安全提示**：首次运行时，macOS可能提示"无法打开，因为它来自身份不明的开发者"
   - 解决方法：打开"系统偏好设置" > "安全性与隐私" > "通用"
   - 点击"仍要打开"按钮

2. **授权验证**：首次运行需要输入授权码
   - 复制显示的机器码
   - 联系管理员获取授权码
   - 输入授权码完成验证

## 使用步骤

1. 启动 LMArenaBridge
2. 在"服务管理"标签页点击"启动"按钮启动API服务器
3. 确保浏览器已安装油猴脚本并启用
4. 访问 LMArena 网站即可使用

## 配置文件

- config.jsonc - 主配置文件
- models.json - 模型配置文件
- .auth - 授权信息（自动生成）

## 端口使用

- 5102 - API服务器端口
- 5103 - ID更新器端口

## 故障排除

1. **无法启动**
   - 检查是否有其他程序占用端口
   - 使用"Kill"按钮强制终止占用端口的进程
   - 查看日志了解详细错误信息

2. **授权问题**
   - 确保机器码没有变化
   - 如需重新授权，在"关于"页面点击"重新授权"

3. **连接问题**
   - 确保防火墙允许应用访问网络
   - 检查API服务器是否正常运行
   - 确认油猴脚本已正确安装和启用

## 技术支持

如遇到问题，请联系：
- 作者vx: tostring1

## 版本信息

- 版本：1.0
- 支持平台：macOS (Intel & Apple Silicon)
'''
    
    with open("dist/使用说明.txt", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ 创建使用说明成功")


def main():
    """主函数"""
    print("=== LMArenaBridge macOS 打包脚本 ===\n")
    
    # 显示运行环境
    if is_ci_environment():
        print("✓ 在 CI 环境中运行")
    else:
        print("✓ 在本地环境中运行")
    
    # 1. 检查环境
    if not check_environment():
        print("\n环境检查失败，请解决上述问题后重试")
        if is_ci_environment():
            sys.exit(1)
        return
    
    # 2. 清理旧文件
    clean_old_files()
    
    # 3. 创建spec文件
    create_spec_file()
    
    # 4. 运行PyInstaller
    if not run_pyinstaller():
        print("\n打包失败，请检查错误信息")
        if is_ci_environment():
            sys.exit(1)
        return
    
    # 5. 创建启动脚本
    create_launch_script()
    
    # 6. 创建说明文件
    create_readme()
    
    # 7. 尝试创建DMG（可选）
    create_dmg()
    
    # 8. 完成
    print("\n" + "="*50)
    print("✓ macOS打包完成！")
    print("="*50)
    print(f"\n输出目录: {os.path.abspath('dist')}")
    print("\n包含文件:")
    print("- LMArenaBridge.app (主应用)")
    print("- 启动LMArenaBridge.command (启动脚本)")
    print("- 使用说明.txt")
    if os.path.exists("dist/LMArenaBridge-macOS.dmg"):
        print("- LMArenaBridge-macOS.dmg (安装包)")
    
    print("\n下一步:")
    print("1. 测试应用是否能正常运行")
    print("2. 分发给macOS用户使用")
    
    # CI 环境中正常退出
    if is_ci_environment():
        sys.exit(0)


if __name__ == "__main__":
    main()
