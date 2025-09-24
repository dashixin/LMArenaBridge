#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LMArenaBridge 集成管理器 - 方案二版本
使用统一入口点方式解决打包问题
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import subprocess
import json
import os
import sys
import time
import requests
from datetime import datetime
import webbrowser
import secrets
import string
from auth_system import AuthSystem


class AuthDialog:
    """授权对话框"""
    def __init__(self, parent, auth_system):
        self.auth_system = auth_system
        self.authorized = False
        self.parent = parent
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("LMArenaBridge 授权验证")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
        # 禁止关闭窗口
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_widgets()
        
        # 确保对话框显示在最前面
        self.dialog.lift()
        self.dialog.focus_force()
        
    def create_widgets(self):
        """创建授权界面组件"""
        # 标题
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(title_frame, text="LMArenaBridge 授权验证", 
                 font=("Arial", 16, "bold")).pack()
        
        # 说明文本
        info_frame = ttk.Frame(self.dialog)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = ("本软件需要授权才能使用。\n"
                    "请将下方的机器码发送给管理员获取授权码。")
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
        
        # 机器码显示
        machine_frame = ttk.LabelFrame(self.dialog, text="您的机器码", padding=10)
        machine_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 获取机器码
        self.machine_code = self.auth_system.get_machine_code()
        
        # 机器码文本框（只读）
        self.machine_code_text = tk.Text(machine_frame, height=2, width=40)
        self.machine_code_text.pack(side=tk.LEFT, padx=(0, 10))
        self.machine_code_text.insert(1.0, self.machine_code)
        self.machine_code_text.config(state=tk.DISABLED)
        
        # 复制按钮
        ttk.Button(machine_frame, text="复制机器码", 
                  command=self.copy_machine_code).pack(side=tk.LEFT)
        
        # 授权码输入
        auth_frame = ttk.LabelFrame(self.dialog, text="输入授权码", padding=10)
        auth_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(auth_frame, text="授权码:").pack(anchor=tk.W)
        
        self.auth_code_var = tk.StringVar()
        self.auth_code_entry = ttk.Entry(auth_frame, textvariable=self.auth_code_var, 
                                       width=40, font=("Consolas", 10))
        self.auth_code_entry.pack(fill=tk.X, pady=5)
        self.auth_code_entry.bind('<Return>', lambda e: self.verify_auth())
        
        # 按钮框架
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(button_frame, text="验证授权码", 
                  command=self.verify_auth).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出程序", 
                  command=self.exit_program).pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(self.dialog, text="", foreground="red")
        self.status_label.pack(pady=10)
        
        # 聚焦到授权码输入框
        self.auth_code_entry.focus()
        
    def copy_machine_code(self):
        """复制机器码到剪贴板"""
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(self.machine_code)
        self.status_label.config(text="机器码已复制到剪贴板", foreground="green")
        
    def verify_auth(self):
        """验证授权码"""
        auth_code = self.auth_code_var.get().strip()
        
        if not auth_code:
            self.status_label.config(text="请输入授权码", foreground="red")
            return
            
        # 验证授权码
        # Import AuthKeyGen for generating auth code
        from auth_keygen import AuthKeyGen
        
        # Create an instance with the secret key
        keygen = AuthKeyGen(b"LMArena_Bridge_2024_Secret_Key_Do_Not_Share")
        expected_auth_code = keygen.generate_auth_code(self.machine_code)
        if auth_code.upper() == expected_auth_code.upper():
            # 保存授权信息
            self.auth_system.save_auth_info(auth_code)
            self.authorized = True
            self.status_label.config(text="授权验证成功！", foreground="green")
            messagebox.showinfo("成功", "授权验证成功！\n程序将正常启动。")
            self.dialog.destroy()
        else:
            self.status_label.config(text="授权码无效，请检查后重试", foreground="red")
            self.auth_code_entry.delete(0, tk.END)
            self.auth_code_entry.focus()
            
    def exit_program(self):
        """退出程序"""
        if messagebox.askyesno("确认", "确定要退出程序吗？"):
            self.dialog.destroy()
            sys.exit(0)
            
    def on_close(self):
        """窗口关闭事件"""
        self.exit_program()
        
    def wait_for_auth(self):
        """等待授权完成"""
        self.dialog.wait_window()
        return self.authorized


class LMArenaManager:
    def __init__(self):
        # 创建根窗口但先不显示
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        
        # 初始化授权系统
        self.auth_system = AuthSystem()
        
        # 检查授权
        if not self.check_authorization():
            # 确保主窗口已经完全初始化
            self.root.update_idletasks()
            
            # 显示授权对话框
            auth_dialog = AuthDialog(self.root, self.auth_system)
            if not auth_dialog.wait_for_auth():
                # 用户没有成功授权，退出程序
                sys.exit(0)
        
        # 授权成功，显示主窗口
        self.root.deiconify()  # 显示主窗口
        self.root.title("LMArenaBridge 管理器 v1.0 (已授权)")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 服务进程管理
        self.api_server_process = None
        self.is_updating_id = False # 添加一个锁来防止并发更新
        self.id_updater_killed_intentionally = False # 用于标记ID更新是否被用户手动终止
        
        # 配置数据
        self.config_data = {}
        self.models_data = {}
        
        # 创建界面
        self.create_widgets()
        self.load_initial_data()
        
        # 启动状态监控
        self.start_status_monitoring()
        
    def check_authorization(self):
        """检查授权状态"""
        return self.auth_system.is_authorized()
        
    def create_widgets(self):
        """创建主界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_service_tab()
        self.create_config_tab()
        self.create_model_tab()
        self.create_status_tab()
        self.create_about_tab()  # 新增关于标签页
        
        # 创建状态栏
        self.create_status_bar(main_frame)
        
    def create_service_tab(self):
        """创建服务管理标签页"""
        service_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(service_frame, text="服务管理")

        # 使用 PanedWindow 分割控制区和日志区
        paned_window = ttk.PanedWindow(service_frame, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # --- 服务控制区域 ---
        control_frame = ttk.LabelFrame(paned_window, text="服务状态与控制", padding=10)
        paned_window.add(control_frame, weight=0) # weight=0, initial size is minimal

        control_frame.grid_columnconfigure(1, weight=1) # Allow status label to expand

        # API 服务器行
        ttk.Label(control_frame, text="API 服务器:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        
        self.api_service_status_label = ttk.Label(control_frame, text="○ 已停止", foreground="red")
        self.api_service_status_label.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W)

        btn_frame_api = ttk.Frame(control_frame)
        btn_frame_api.grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
        
        self.start_api_btn = ttk.Button(btn_frame_api, text="启动", command=self.start_api_server, width=8)
        self.start_api_btn.pack(side=tk.LEFT, padx=2)
        self.stop_api_btn = ttk.Button(btn_frame_api, text="停止", command=self.stop_api_server, state=tk.DISABLED, width=8)
        self.stop_api_btn.pack(side=tk.LEFT, padx=2)
        self.kill_api_btn = ttk.Button(btn_frame_api, text="Kill", command=self.kill_api_server_by_port, width=5)
        self.kill_api_btn.pack(side=tk.LEFT, padx=2)

        # --- 日志显示区域 ---
        log_container = ttk.Frame(paned_window)
        paned_window.add(log_container, weight=1)

        log_frame = ttk.LabelFrame(log_container, text="服务日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日志工具栏
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(log_toolbar, text="导出日志", command=self.export_log).pack(side=tk.RIGHT, padx=5)
        ttk.Button(log_toolbar, text="清空日志", command=self.clear_log).pack(side=tk.RIGHT)

        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def create_config_tab(self):
        """创建配置管理标签页"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="配置管理")
        
        # 基本配置区域
        basic_frame = ttk.LabelFrame(config_frame, text="基本配置", padding=10)
        basic_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # API密钥设置
        api_key_frame = ttk.Frame(basic_frame)
        api_key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_key_frame, text="API密钥:").pack(side=tk.LEFT)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(api_key_frame, textvariable=self.api_key_var, width=30)
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(api_key_frame, text="生成随机密钥", command=self.generate_api_key).pack(side=tk.LEFT, padx=5)
        
        # 会话管理区域
        session_frame = ttk.LabelFrame(config_frame, text="会话管理", padding=10)
        session_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 会话ID显示
        session_id_frame = ttk.Frame(session_frame)
        session_id_frame.pack(fill=tk.X, pady=2)
        ttk.Label(session_id_frame, text="当前会话ID:").pack(side=tk.LEFT)
        self.session_id_label = ttk.Label(session_id_frame, text="未加载", foreground="gray")
        self.session_id_label.pack(side=tk.LEFT, padx=10)
        
        message_id_frame = ttk.Frame(session_frame)
        message_id_frame.pack(fill=tk.X, pady=2)
        ttk.Label
