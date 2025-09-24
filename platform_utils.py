#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台工具函数
处理跨平台差异
"""

import sys
import platform
import subprocess
import os


def get_platform():
    """获取当前平台"""
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return "unknown"


def get_platform_info():
    """获取详细的平台信息"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "platform": get_platform()
    }


def kill_process_by_port(port):
    """根据端口号终止进程（跨平台）"""
    current_platform = get_platform()
    
    if current_platform == "windows":
        # Windows: 使用 netstat 和 taskkill
        find_cmd = f"netstat -ano | findstr LISTENING | findstr :{port}"
        result = subprocess.run(find_cmd, capture_output=True, text=True, shell=True, encoding='utf-8', errors='ignore')
        output = result.stdout.strip()
        
        killed_pids = []
        if output:
            for line in output.splitlines():
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    kill_cmd = f"taskkill /F /PID {pid}"
                    kill_result = subprocess.run(kill_cmd, capture_output=True, text=True, shell=True)
                    if kill_result.returncode == 0:
                        killed_pids.append(pid)
        return killed_pids
        
    elif current_platform in ["macos", "linux"]:
        # macOS/Linux: 使用 lsof 和 kill
        find_cmd = f"lsof -t -i:{port} -sTCP:LISTEN"
        result = subprocess.run(find_cmd, capture_output=True, text=True, shell=True)
        pids = result.stdout.strip().split()
        
        killed_pids = []
        if pids:
            for pid in pids:
                kill_cmd = f"kill -9 {pid}"
                kill_result = subprocess.run(kill_cmd, capture_output=True, text=True, shell=True)
                if kill_result.returncode == 0:
                    killed_pids.append(pid)
        return killed_pids
    
    return []


def get_startup_info():
    """获取子进程启动信息（Windows需要隐藏控制台）"""
    if get_platform() == "windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def get_process_creation_flags():
    """获取进程创建标志（Windows需要）"""
    if get_platform() == "windows":
        return subprocess.CREATE_NO_WINDOW
    return 0


def open_file_or_url(path):
    """跨平台打开文件或URL"""
    current_platform = get_platform()
    
    if current_platform == "windows":
        os.startfile(path)
    elif current_platform == "macos":
        subprocess.run(["open", path])
    elif current_platform == "linux":
        subprocess.run(["xdg-open", path])
    else:
        # 尝试使用webbrowser作为后备方案
        import webbrowser
        webbrowser.open(path)


def get_home_directory():
    """获取用户主目录"""
    return os.path.expanduser("~")


def ensure_utf8_environment():
    """确保UTF-8环境（主要针对Windows）"""
    env = os.environ.copy()
    
    if get_platform() == "windows":
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        
        # 尝试设置控制台代码页
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except:
            pass
    
    return env
