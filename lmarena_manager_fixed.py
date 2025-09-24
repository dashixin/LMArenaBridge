#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LMArenaBridge 集成管理器 - 修复打包问题版本
修复了打包后重复启动 GUI 的问题
"""

# 在文件开头添加这些辅助函数
def get_resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def is_frozen():
    """检查是否在打包后的环境中运行"""
    return getattr(sys, 'frozen', False)

# 修改 start_api_server 方法
def start_api_server(self):
    """启动API服务器"""
    try:
        if self.api_server_process and self.api_server_process.poll() is None:
            messagebox.showwarning("警告", "API服务器已在运行中")
            return
            
        self.log_message("正在启动API服务器...")
        
        # 设置环境变量，强制子进程使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        
        # 根据运行环境选择不同的启动方式
        if is_frozen():
            # 在打包后的环境中，使用打包的 api_server.py
            api_server_path = get_resource_path("api_server.py")
            # 需要明确指定 Python 解释器
            # 方案1：使用系统 Python（需要用户安装 Python）
            # python_exe = "python"
            
            # 方案2：使用嵌入式 Python（需要在打包时包含）
            # python_exe = get_resource_path("python/python.exe")
            
            # 方案3：将 api_server 作为模块导入并在线程中运行
            # 这是最可靠的方案
            import threading
            from api_server import run_server  # 需要 api_server.py 支持这种调用方式
            
            self.api_thread = threading.Thread(target=run_server, daemon=True)
            self.api_thread.start()
            
            self.log_message("API服务器已在线程中启动")
            self.start_api_btn.config(state=tk.DISABLED)
            self.stop_api_btn.config(state=tk.NORMAL)
            return
        else:
            # 在开发环境中，正常使用 subprocess
            self.api_server_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env
            )
        
        # 启动日志监控线程
        threading.Thread(target=self.monitor_api_server_output, daemon=True).start()
        
        self.start_api_btn.config(state=tk.DISABLED)
        self.stop_api_btn.config(state=tk.NORMAL)
        
        self.log_message("API服务器启动命令已发送")
        
    except Exception as e:
        self.log_message(f"启动API服务器失败: {e}", "ERROR")
        messagebox.showerror("错误", f"启动API服务器失败: {e}")

# 修改 _run_id_updater_process 方法
def _run_id_updater_process(self, mode):
    """在单独的线程中运行 id_updater.py 进程"""
    try:
        # 重置标志
        self.id_updater_killed_intentionally = False
        
        self.log_message(f"正在以 {mode} 模式启动会话ID更新...")
        
        # 弹出提示框，指导用户操作
        self.root.after(0, lambda: messagebox.showinfo("提示",
            "ID更新程序已启动。\n\n"
            "请在浏览器中进行以下操作：\n"
            "1. 确保LMArena页面已打开。\n"
            "2. 进入对应的对话模式。\n"
            "3. 点击任意模型回答右上角的 'Retry' 按钮来捕获ID。\n\n"
            "完成后，配置将自动刷新。"))

        if is_frozen():
            # 在打包环境中，使用不同的方式运行 id_updater
            # 方案：将 id_updater 作为模块导入
            import id_updater
            
            # 模拟用户输入
            if mode == 'direct_chat':
                result = id_updater.run_with_mode('a')
            elif mode == 'battle':
                result = id_updater.run_with_mode('b', 'A')
            
            if result:
                self.log_message("会话ID更新成功！")
                self.root.after(0, self.on_id_update_success)
            else:
                if not self.id_updater_killed_intentionally:
                    self.log_message("会话ID更新失败", "ERROR")
                    self.root.after(0, lambda: messagebox.showerror("错误", "会话ID更新失败，请查看日志获取详细信息。"))
        else:
            # 在开发环境中，使用原有的 subprocess 方式
            # ... 原有代码保持不变 ...
            pass
            
    except Exception as e:
        if not self.id_updater_killed_intentionally:
            self.log_message(f"执行 id_updater.py 时出错: {e}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", f"执行 id_updater.py 时出错: {e}"))
    finally:
        # 确保在线程结束时释放锁
        self.is_updating_id = False
