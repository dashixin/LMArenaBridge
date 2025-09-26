#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LMArenaBridge 集成管理器 - 带授权版本
一个简单易用的GUI应用程序，集成LMArenaBridge项目的所有核心功能
包含一机一码授权系统
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
from platform_utils import (
    get_platform, 
    kill_process_by_port as platform_kill_process,
    get_startup_info,
    get_process_creation_flags,
    ensure_utf8_environment
)


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
        ttk.Label(message_id_frame, text="当前消息ID:").pack(side=tk.LEFT)
        self.message_id_label = ttk.Label(message_id_frame, text="未加载", foreground="gray")
        self.message_id_label.pack(side=tk.LEFT, padx=10)
        
        # 模式选择和更新按钮
        mode_frame = ttk.Frame(session_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mode_frame, text="模式:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar()
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, values=["direct_chat", "battle"], state="readonly", width=15)
        mode_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(mode_frame, text="更新会话ID", command=self.update_session_id).pack(side=tk.LEFT, padx=10)
        ttk.Button(mode_frame, text="结束会话更新", command=self.kill_session_updater_by_port).pack(side=tk.LEFT, padx=5)
        
        # 配置操作按钮
        config_btn_frame = ttk.Frame(config_frame)
        config_btn_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(config_btn_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="重新加载配置", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btn_frame, text="重置为默认值", command=self.reset_config).pack(side=tk.LEFT, padx=5)
        
    def create_model_tab(self):
        """创建模型管理标签页"""
        model_frame = ttk.Frame(self.notebook)
        self.notebook.add(model_frame, text="模型管理")
        
        # 模型列表区域
        list_frame = ttk.LabelFrame(model_frame, text="可用模型列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 工具栏
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(toolbar_frame, text="更新模型列表", command=self.update_model_list).pack(side=tk.RIGHT, padx=5)
        ttk.Label(toolbar_frame, text="双击模型名称可编辑").pack(side=tk.LEFT)
        
        # 模型列表
        columns = ("name", "type", "id", "status")
        self.model_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        self.model_tree.heading("name", text="模型名称")
        self.model_tree.heading("type", text="类型")
        self.model_tree.heading("id", text="模型ID")
        self.model_tree.heading("status", text="状态")
        
        self.model_tree.column("name", width=200)
        self.model_tree.column("type", width=80)
        self.model_tree.column("id", width=300)
        self.model_tree.column("status", width=80)
        
        # 添加滚动条
        model_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=model_scrollbar.set)
        
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        model_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 模型操作区域
        operation_frame = ttk.LabelFrame(model_frame, text="模型操作", padding=10)
        operation_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(operation_frame, text="添加新模型", command=self.add_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(operation_frame, text="删除选中模型", command=self.delete_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(operation_frame, text="编辑模型映射", command=self.edit_model_mapping).pack(side=tk.LEFT, padx=5)
        
    def create_status_tab(self):
        """创建状态监控标签页"""
        status_frame = ttk.Frame(self.notebook)
        self.notebook.add(status_frame, text="状态监控")
        
        # 连接状态区域
        connection_frame = ttk.LabelFrame(status_frame, text="连接状态", padding=10)
        connection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态显示
        self.api_status_label = ttk.Label(connection_frame, text="API服务器: ○ 已停止")
        self.api_status_label.pack(anchor=tk.W, pady=2)
        
        self.websocket_status_label = ttk.Label(connection_frame, text="WebSocket: ○ 未连接")
        self.websocket_status_label.pack(anchor=tk.W, pady=2)
        
        self.browser_status_label = ttk.Label(connection_frame, text="浏览器页面: ○ 未检测到")
        self.browser_status_label.pack(anchor=tk.W, pady=2)
        
        # 快速测试区域
        test_frame = ttk.LabelFrame(status_frame, text="快速测试", padding=10)
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(test_frame, text="测试API连接", command=self.test_api_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="测试模型响应", command=self.test_model_response).pack(side=tk.LEFT, padx=5)
        ttk.Button(test_frame, text="诊断常见问题", command=self.diagnose_issues).pack(side=tk.LEFT, padx=5)
        
        # 系统信息区域
        info_frame = ttk.LabelFrame(status_frame, text="系统信息", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.python_version_label = ttk.Label(info_frame, text=f"Python版本: {sys.version.split()[0]}")
        self.python_version_label.pack(anchor=tk.W, pady=2)
        
        self.dependency_status_label = ttk.Label(info_frame, text="依赖状态: 检查中...")
        self.dependency_status_label.pack(anchor=tk.W, pady=2)
        
        self.config_status_label = ttk.Label(info_frame, text="配置状态: 检查中...")
        self.config_status_label.pack(anchor=tk.W, pady=2)
        
    def create_about_tab(self):
        """创建关于标签页，显示授权信息"""
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="关于")
        
        # 软件信息
        info_frame = ttk.LabelFrame(about_frame, text="软件信息", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="LMArenaBridge 管理器", 
                 font=("Arial", 14, "bold")).pack(pady=5)
        ttk.Label(info_frame, text="版本: 1.0").pack()
        ttk.Label(info_frame, text="作者vx: tostring1").pack()
        
        # 授权信息
        auth_frame = ttk.LabelFrame(about_frame, text="授权信息", padding=10)
        auth_frame.pack(fill=tk.X, padx=5, pady=5)
        
        auth_status = self.auth_system.get_auth_status()
        
        ttk.Label(auth_frame, text=f"授权状态: {'已授权' if auth_status['authorized'] else '未授权'}", 
                 foreground="green" if auth_status['authorized'] else "red").pack(anchor=tk.W, pady=2)
        ttk.Label(auth_frame, text=f"机器码: {auth_status['machine_code']}").pack(anchor=tk.W, pady=2)
        
        if auth_status['authorized'] and auth_status.get('auth_date'):
            auth_date = datetime.fromisoformat(auth_status['auth_date']).strftime('%Y-%m-%d %H:%M:%S')
            ttk.Label(auth_frame, text=f"授权时间: {auth_date}").pack(anchor=tk.W, pady=2)
            
        # 重新授权按钮
        ttk.Button(auth_frame, text="重新授权", command=self.reauthorize).pack(pady=10)
        
    def reauthorize(self):
        """重新授权"""
        if messagebox.askyesno("确认", "确定要重新授权吗？\n这将清除当前的授权信息。"):
            # 删除授权文件
            if os.path.exists(self.auth_system.auth_file):
                os.remove(self.auth_system.auth_file)
            messagebox.showinfo("提示", "授权信息已清除，请重新启动程序进行授权。")
            self.root.quit()
            sys.exit(0)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        self.status_text = ttk.Label(self.status_bar, text="就绪")
        self.status_text.pack(side=tk.LEFT)
        
        # 服务状态指示器
        self.api_indicator = ttk.Label(self.status_bar, text="API服务器: ○已停止", foreground="red")
        self.api_indicator.pack(side=tk.RIGHT, padx=10)
        
    # ==================== 数据加载和保存 ====================
    
    def load_initial_data(self):
        """加载初始数据"""
        try:
            self.load_config()
        except Exception as e:
            print(f"加载配置时出错: {e}")
            # 继续运行，使用默认配置
            
        try:
            self.load_models()
        except Exception as e:
            print(f"加载模型时出错: {e}")
            # 继续运行，使用空模型列表
            
        try:
            self.check_dependencies()
        except Exception as e:
            print(f"检查依赖时出错: {e}")
            # 继续运行
        
    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.jsonc', 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单的JSONC解析（移除注释）
                lines = content.splitlines()
                clean_lines = []
                for line in lines:
                    if '//' in line:
                        line = line[:line.index('//')]
                    clean_lines.append(line)
                clean_content = '\n'.join(clean_lines)
                self.config_data = json.loads(clean_content)
                
            # 更新界面
            self.api_key_var.set(self.config_data.get('api_key', ''))
            self.mode_var.set(self.config_data.get('id_updater_last_mode', 'direct_chat'))
            
            # 更新会话ID显示
            session_id = self.config_data.get('session_id', '未设置')
            message_id = self.config_data.get('message_id', '未设置')
            self.session_id_label.config(text=session_id[:8] + "..." if len(session_id) > 8 else session_id)
            self.message_id_label.config(text=message_id[:8] + "..." if len(message_id) > 8 else message_id)
            
            self.log_message("配置文件加载成功")
            
        except Exception as e:
            self.log_message(f"加载配置文件失败: {e}", "ERROR")
            messagebox.showerror("错误", f"加载配置文件失败: {e}")
            
    def load_models(self):
        """加载模型列表"""
        try:
            with open('models.json', 'r', encoding='utf-8') as f:
                self.models_data = json.load(f)
                
            # 更新模型列表显示
            self.refresh_model_list()
            self.log_message(f"模型列表加载成功，共{len(self.models_data)}个模型")
            
        except Exception as e:
            self.log_message(f"加载模型列表失败: {e}", "ERROR")
            
    def save_config(self):
        """保存配置文件"""
        try:
            # 更新配置数据
            self.config_data['api_key'] = self.api_key_var.get()
            self.config_data['id_updater_last_mode'] = self.mode_var.get()
            
            # 读取原文件保留注释
            with open('config.jsonc', 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # 简单的替换策略（保留原有格式）
            import re
            for key, value in self.config_data.items():
                if isinstance(value, bool):
                    value_str = 'true' if value else 'false'
                elif isinstance(value, str):
                    value_str = f'"{value}"'
                else:
                    value_str = str(value)
                    
                pattern = rf'("{key}"\s*:\s*)[^,\n}}]+'
                replacement = rf'\1{value_str}'
                original_content = re.sub(pattern, replacement, original_content)
                
            with open('config.jsonc', 'w', encoding='utf-8') as f:
                f.write(original_content)
                
            self.log_message("配置保存成功")
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            self.log_message(f"保存配置失败: {e}", "ERROR")
            messagebox.showerror("错误", f"保存配置失败: {e}")
            
    # ==================== 服务管理 ====================
    
    def start_api_server(self):
        """启动API服务器"""
        try:
            if self.api_server_process and self.api_server_process.poll() is None:
                messagebox.showwarning("警告", "API服务器已在运行中")
                return
                
            self.log_message("正在启动API服务器...")
            
            # 使用平台工具获取环境和启动信息
            env = ensure_utf8_environment()
            startupinfo = get_startup_info()
            
            self.api_server_process = subprocess.Popen(
                [sys.executable, "api_server.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                env=env,
                startupinfo=startupinfo
            )
            
            # 启动日志监控线程
            threading.Thread(target=self.monitor_api_server_output, daemon=True).start()
            
            self.start_api_btn.config(state=tk.DISABLED)
            self.stop_api_btn.config(state=tk.NORMAL)
            
            self.log_message("API服务器启动命令已发送")
            
        except Exception as e:
            self.log_message(f"启动API服务器失败: {e}", "ERROR")
            messagebox.showerror("错误", f"启动API服务器失败: {e}")
            
    def stop_api_server(self):
        """停止API服务器"""
        try:
            if self.api_server_process and self.api_server_process.poll() is None:
                pid = self.api_server_process.pid
                if sys.platform == "win32":
                    # 在Windows上，使用taskkill强制终止进程及其所有子进程
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], check=True, capture_output=True)
                else:
                    # 在其他系统上，使用terminate/kill
                    self.api_server_process.terminate()
                    try:
                        self.api_server_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.api_server_process.kill()
                
                self.api_server_process = None
            
            self.start_api_btn.config(state=tk.NORMAL)
            self.stop_api_btn.config(state=tk.DISABLED)
            
            self.log_message("API服务器已停止")
            
        except Exception as e:
            self.log_message(f"停止API服务器失败: {e}", "ERROR")
            
    def kill_api_server_by_port(self):
        """通过端口号强制终止API服务器进程"""
        port = 5102
        if not messagebox.askyesno("确认操作", f"您确定要强制终止占用端口 {port} 的所有进程吗？\n这可能导致数据丢失或服务异常。"):
            return

        self.log_message(f"正在尝试强制终止占用端口 {port} 的进程...", "WARN")
        threading.Thread(target=self._kill_process_on_port, args=(port,), daemon=True).start()

    def _kill_process_on_port(self, port):
        """在后台线程中执行终止操作"""
        try:
            # 使用平台工具终止进程
            killed_pids = platform_kill_process(port)
            
            if killed_pids:
                for pid in killed_pids:
                    self.log_message(f"成功终止进程 PID: {pid}", "INFO")
            else:
                self.log_message(f"未找到监听端口 {port} 的活动进程。")
            
            if killed_pids:
                self.root.after(0, lambda: messagebox.showinfo("成功", f"已强制终止占用端口 {port} 的进程: {', '.join(killed_pids)}"))
                # 如果被杀死的进程是管理器启动的，则更新UI状态
                if self.api_server_process and str(self.api_server_process.pid) in killed_pids:
                    self.api_server_process = None
                    self.root.after(0, self.stop_api_server) # 调用stop来重置按钮状态
            else:
                self.log_message(f"未找到监听端口 {port} 的活动进程。")
                self.root.after(0, lambda: messagebox.showinfo("提示", f"未找到监听端口 {port} 的活动进程。"))

        except Exception as e:
            error_msg = f"强制终止进程时出错: {e}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            
    def kill_session_updater_by_port(self):
        """通过端口号强制终止会话更新进程"""
        port = 5103
        # 标志用户主动终止
        self.id_updater_killed_intentionally = True
        self.log_message(f"正在尝试强制终止占用端口 {port} 的进程...", "WARN")
        threading.Thread(target=self._kill_session_updater_process, args=(port,), daemon=True).start()

    def _kill_session_updater_process(self, port):
        """在后台线程中执行终止会话更新进程的操作"""
        try:
            # 使用平台工具终止进程
            killed_pids = platform_kill_process(port)
            
            if killed_pids:
                for pid in killed_pids:
                    self.log_message(f"成功终止进程 PID: {pid}", "INFO")
            else:
                self.log_message(f"未找到监听端口 {port} 的活动进程。")
            
            if killed_pids:
                self.root.after(0, lambda: messagebox.showinfo("成功", f"已强制终止占用端口 {port} 的进程: {', '.join(killed_pids)}"))
            else:
                self.log_message(f"未找到监听端口 {port} 的活动进程。")
                self.root.after(0, lambda: messagebox.showinfo("提示", f"未找到监听端口 {port} 的活动进程。"))

        except Exception as e:
            error_msg = f"强制终止进程时出错: {e}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
            
    def start_all_services(self):
        """启动所有服务"""
        self.start_api_server()
            
    def stop_all_services(self):
        """停止所有服务"""
        self.stop_api_server()
        
    # ==================== 日志管理 ====================
    
    def log_message(self, message, level="INFO"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 更新状态栏
        self.status_text.config(text=message)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def export_log(self):
        """导出日志"""
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出日志失败: {e}")
                
    def monitor_api_server_output(self):
        """监控API服务器输出"""
        if not self.api_server_process:
            return
            
        try:
            for line in iter(self.api_server_process.stdout.readline, ''):
                if line:
                    # 确保line是字符串类型，处理可能的编码问题
                    if isinstance(line, bytes):
                        line = line.decode('utf-8', errors='replace')
                    # 移除特殊字符和控制字符
                    line = line.strip()
                    # 过滤掉空行
                    if line:
                        # 使用安全的方式传递日志消息
                        self.root.after(0, self.log_message, f"[API] {line}")
                if self.api_server_process.poll() is not None:
                    break
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"[API] 监控输出时出错: {e}", "ERROR"))
            
    # ==================== 配置管理 ====================
    
    def generate_api_key(self):
        """生成随机API密钥"""
        key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        self.api_key_var.set(key)
        self.log_message("已生成新的API密钥")
        
    def reset_config(self):
        """重置配置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有配置为默认值吗？"):
            self.api_key_var.set("")
            self.mode_var.set("direct_chat")
            self.log_message("配置已重置为默认值")
            
    def update_session_id(self):
        """更新会话ID"""
        if self.is_updating_id:
            messagebox.showwarning("提示", "一个ID更新任务已经在运行中，请稍候...")
            return

        # 检查API服务器是否运行
        if not self.api_server_process or self.api_server_process.poll() is not None:
            messagebox.showerror("错误", "请先启动API服务器")
            return

        mode = self.mode_var.get()
        if not mode:
            messagebox.showerror("错误", "请先选择一个模式 (direct_chat 或 battle)")
            return

        # 使用线程来运行 id_updater.py 以免阻塞GUI
        self.is_updating_id = True
        threading.Thread(target=self._run_id_updater_process, args=(mode,), daemon=True).start()

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

            # 使用平台工具获取进程创建参数
            creationflags = get_process_creation_flags()
            env = ensure_utf8_environment()
            startupinfo = get_startup_info()

            process = subprocess.Popen(
                [sys.executable, "id_updater.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags,
                env=env,
                startupinfo=startupinfo
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

    def on_id_update_success(self):
        """ID更新成功后的回调函数"""
        self.load_config()
        messagebox.showinfo("成功", "会话ID已成功更新！")
            
    # ==================== 模型管理 ====================
    
    def refresh_model_list(self):
        """刷新模型列表显示"""
        # 清空现有列表
        for item in self.model_tree.get_children():
            self.model_tree.delete(item)
            
        # 添加模型数据
        for name, value in self.models_data.items():
            if isinstance(value, str):
                if ':' in value:
                    model_id, model_type = value.split(':', 1)
                else:
                    model_id = value
                    model_type = "text"
            else:
                model_id = str(value)
                model_type = "text"
                
            status = "已配置"
            self.model_tree.insert("", tk.END, values=(name, model_type, model_id, status))
            
    def update_model_list(self):
        """更新模型列表"""
        try:
            # 检查API服务器是否运行
            if not self.api_server_process or self.api_server_process.poll() is not None:
                messagebox.showerror("错误", "请先启动API服务器")
                return
                
            self.log_message("正在请求更新模型列表...")
            
            # 发送模型更新请求
            response = requests.post("http://127.0.0.1:5102/internal/request_model_update", timeout=10)
            if response.status_code == 200:
                self.log_message("模型列表更新请求已发送，请等待浏览器处理...")
                messagebox.showinfo("提示", "模型列表更新请求已发送！\n\n请确保LMArena页面已打开，系统将自动抓取最新模型列表并保存到available_models.json文件中。")
            else:
                self.log_message(f"模型更新请求失败: {response.text}", "ERROR")
                
        except requests.RequestException as e:
            self.log_message(f"连接API服务器失败: {e}", "ERROR")
            messagebox.showerror("错误", f"连接API服务器失败: {e}")
        except Exception as e:
            self.log_message(f"更新模型列表失败: {e}", "ERROR")
            
    def add_model(self):
        """添加新模型"""
        dialog = ModelEditDialog(self.root, "添加模型")
        if dialog.result:
            name, model_id, model_type = dialog.result
            if model_type == "image":
                self.models_data[name] = f"{model_id}:image"
            else:
                self.models_data[name] = model_id
                
            self.save_models()
            self.refresh_model_list()
            self.log_message(f"已添加模型: {name}")
            
    def delete_model(self):
        """删除选中的模型"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的模型")
            return
            
        item = selection[0]
        model_name = self.model_tree.item(item)['values'][0]
        
        if messagebox.askyesno("确认", f"确定要删除模型 '{model_name}' 吗？"):
            if model_name in self.models_data:
                del self.models_data[model_name]
                self.save_models()
                self.refresh_model_list()
                self.log_message(f"已删除模型: {model_name}")
                
    def edit_model_mapping(self):
        """编辑模型映射"""
        messagebox.showinfo("提示", "模型映射编辑功能将在后续版本中实现")
        
    def save_models(self):
        """保存模型列表"""
        try:
            with open('models.json', 'w', encoding='utf-8') as f:
                json.dump(self.models_data, f, indent=4, ensure_ascii=False)
            self.log_message("模型列表已保存")
        except Exception as e:
            self.log_message(f"保存模型列表失败: {e}", "ERROR")
            
    # ==================== 状态监控 ====================
    
    def start_status_monitoring(self):
        """启动状态监控"""
        self.update_status()
        self.root.after(5000, self.start_status_monitoring)  # 每5秒更新一次
        
    def update_status(self):
        """更新状态显示"""
        # 检查API服务器状态
        api_running = self.api_server_process and self.api_server_process.poll() is None
        if api_running:
            self.api_status_label.config(text="API服务器: ● 运行中 (端口5102)", foreground="green")
            self.api_indicator.config(text="API服务器: ●运行中", foreground="green")
            self.api_service_status_label.config(text="● 运行中", foreground="green")
        else:
            self.api_status_label.config(text="API服务器: ○ 已停止", foreground="red")
            self.api_indicator.config(text="API服务器: ○已停止", foreground="red")
            self.api_service_status_label.config(text="○ 已停止", foreground="red")
            
        # 检查WebSocket连接状态
        self.check_websocket_status()
        
    def check_websocket_status(self):
        """检查WebSocket连接状态"""
        try:
            if self.api_server_process and self.api_server_process.poll() is None:
                # 这里可以添加更详细的WebSocket状态检查
                self.websocket_status_label.config(text="WebSocket: ● 服务可用", foreground="green")
            else:
                self.websocket_status_label.config(text="WebSocket: ○ 服务未启动", foreground="red")
        except:
            self.websocket_status_label.config(text="WebSocket: ○ 未连接", foreground="red")
            
    def check_dependencies(self):
        """检查依赖状态"""
        # 使用线程来检查依赖，避免阻塞主线程
        def check_deps():
            try:
                import fastapi
                import uvicorn
                import packaging
                self.root.after(0, lambda: self.dependency_status_label.config(
                    text="依赖状态: ✓ 所有依赖已安装", foreground="green"))
            except ImportError as e:
                self.root.after(0, lambda: self.dependency_status_label.config(
                    text=f"依赖状态: ✗ 缺少依赖: {e.name}", foreground="red"))
        
        # 在后台线程中检查依赖
        threading.Thread(target=check_deps, daemon=True).start()
            
        # 检查配置文件状态
        config_ok = os.path.exists('config.jsonc') and os.path.exists('models.json')
        if config_ok:
            self.config_status_label.config(text="配置状态: ✓ 配置文件完整", foreground="green")
        else:
            self.config_status_label.config(text="配置状态: ✗ 配置文件缺失", foreground="red")
            
    def test_api_connection(self):
        """测试API连接"""
        try:
            response = requests.get("http://127.0.0.1:5102/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                count = len(models.get('data', []))
                self.log_message(f"API连接测试成功，发现{count}个可用模型")
                messagebox.showinfo("成功", f"API连接正常！\n发现{count}个可用模型")
            else:
                self.log_message(f"API连接测试失败: HTTP {response.status_code}", "ERROR")
                messagebox.showerror("错误", f"API连接失败: HTTP {response.status_code}")
        except requests.RequestException as e:
            self.log_message(f"API连接测试失败: {e}", "ERROR")
            messagebox.showerror("错误", f"API连接失败: {e}")
            
    def test_model_response(self):
        """测试模型响应"""
        if not self.models_data:
            messagebox.showwarning("警告", "没有配置任何模型")
            return
            
        # 选择第一个模型进行测试
        model_name = list(self.models_data.keys())[0]
        
        try:
            test_data = {
                "model": model_name,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }
            
            headers = {}
            if self.api_key_var.get():
                headers["Authorization"] = f"Bearer {self.api_key_var.get()}"
                
            response = requests.post(
                "http://127.0.0.1:5102/v1/chat/completions",
                json=test_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_message(f"模型 {model_name} 响应测试成功")
                messagebox.showinfo("成功", f"模型 {model_name} 响应正常！")
            else:
                self.log_message(f"模型响应测试失败: HTTP {response.status_code}", "ERROR")
                messagebox.showerror("错误", f"模型响应失败: {response.text}")
                
        except requests.RequestException as e:
            self.log_message(f"模型响应测试失败: {e}", "ERROR")
            messagebox.showerror("错误", f"模型响应测试失败: {e}")
            
    def diagnose_issues(self):
        """诊断常见问题"""
        issues = []
        
        # 检查服务状态
        if not (self.api_server_process and self.api_server_process.poll() is None):
            issues.append("• API服务器未运行")
            
        # 检查配置文件
        if not os.path.exists('config.jsonc'):
            issues.append("• config.jsonc 文件不存在")
        if not os.path.exists('models.json'):
            issues.append("• models.json 文件不存在")
            
        # 检查会话ID
        if self.config_data.get('session_id', '').startswith('YOUR_'):
            issues.append("• 会话ID未配置或使用默认值")
            
        # 检查模型配置
        if not self.models_data:
            issues.append("• 没有配置任何模型")
            
        if issues:
            issue_text = "发现以下问题：\n\n" + "\n".join(issues)
            issue_text += "\n\n建议：\n"
            issue_text += "1. 确保API服务器正在运行\n"
            issue_text += "2. 检查配置文件是否存在且格式正确\n"
            issue_text += "3. 运行会话ID更新流程\n"
            issue_text += "4. 确保浏览器已打开LMArena页面并安装油猴脚本"
            
            messagebox.showwarning("诊断结果", issue_text)
            self.log_message(f"诊断发现{len(issues)}个问题")
        else:
            messagebox.showinfo("诊断结果", "未发现明显问题，系统状态良好！")
            self.log_message("系统诊断通过")
        
    def run(self):
        """运行应用程序"""
        self.root.mainloop()


class ModelEditDialog:
    """模型编辑对话框"""
    def __init__(self, parent, title):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建对话框组件"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模型名称
        ttk.Label(main_frame, text="模型名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, pady=5)
        
        # 模型ID
        ttk.Label(main_frame, text="模型ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.id_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.id_var, width=30).grid(row=1, column=1, pady=5)
        
        # 模型类型
        ttk.Label(main_frame, text="模型类型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="text")
        type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=["text", "image"], state="readonly", width=27)
        type_combo.grid(row=2, column=1, pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.cancel_clicked).pack(side=tk.LEFT, padx=5)
        
        # 等待对话框关闭
        self.dialog.wait_window()
        
    def ok_clicked(self):
        """确定按钮点击"""
        name = self.name_var.get().strip()
        model_id = self.id_var.get().strip()
        model_type = self.type_var.get()
        
        if not name or not model_id:
            messagebox.showerror("错误", "请填写完整的模型信息")
            return
            
        self.result = (name, model_id, model_type)
        self.dialog.destroy()
        
    def cancel_clicked(self):
        """取消按钮点击"""
        self.dialog.destroy()


# 主程序入口
if __name__ == "__main__":
    try:
        app = LMArenaManager()
        app.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()
