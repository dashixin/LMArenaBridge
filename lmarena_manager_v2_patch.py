#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案二的关键修改部分
将这些方法替换到原始的 lmarena_manager.py 中
"""

# 在 LMArenaManager 类中替换以下方法：

def start_api_server(self):
    """启动API服务器 - 方案二版本"""
    try:
        if self.api_server_process and self.api_server_process.poll() is None:
            messagebox.showwarning("警告", "API服务器已在运行中")
            return
            
        self.log_message("正在启动API服务器...")
        
        # 设置环境变量，强制子进程使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        
        # 使用统一入口点方式调用
        self.api_server_process = subprocess.Popen(
            [sys.executable, "api_server"],  # 作为参数传递给主程序
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

def _run_id_updater_process(self, mode):
    """在单独的线程中运行 id_updater.py 进程 - 方案二版本"""
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

        # 启动 id_updater 进程 - 使用统一入口点
        # 在Windows上，使用 CREATE_NO_WINDOW 标志来隐藏控制台窗口
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        # 设置环境变量，强制子进程使用UTF-8编码
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"

        process = subprocess.Popen(
            [sys.executable, "id_updater"],  # 作为参数传递给主程序
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            creationflags=creationflags,
            env=env
        )

        # 根据 id_updater.py 的要求准备输入
        # 'a' for DirectChat, 'b' for Battle
        user_input = ""
        if mode == 'direct_chat':
            user_input = "a\n"
        elif mode == 'battle':
            # Battle模式需要两次输入: 'b' for mode, then 'A' or 'B' for target.
            # 我们默认选择 'A'，因为脚本提示 search 模型必须用 A。
            user_input = "b\nA\n"
        
        # 通过 communicate 发送所有输入并等待进程结束
        stdout, stderr = process.communicate(input=user_input)

        # 记录进程的输出
        if stdout:
            for line in stdout.splitlines():
                self.log_message(f"[id_updater] {line}")
        if stderr:
            for line in stderr.splitlines():
                self.log_message(f"[id_updater] {line}", "ERROR")

        # 检查进程是否成功完成
        if process.returncode == 0:
            self.log_message("会话ID更新成功！")
            # 在主线程中更新UI
            self.root.after(0, self.on_id_update_success)
        else:
            if self.id_updater_killed_intentionally:
                self.log_message("会话ID更新已被用户主动终止。", "INFO")
                # 不显示错误对话框，因为这是用户主动操作
            else:
                self.log_message(f"会话ID更新失败，id_updater.py 退出代码: {process.returncode}", "ERROR")
                self.root.after(0, lambda: messagebox.showerror("错误", "会话ID更新失败，请查看日志获取详细信息。"))

    except Exception as e:
        if not self.id_updater_killed_intentionally:
            self.log_message(f"执行 id_updater.py 时出错: {e}", "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", f"执行 id_updater.py 时出错: {e}"))
    finally:
        # 确保在线程结束时释放锁
        self.is_updating_id = False
