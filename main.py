#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LMArenaBridge 统一入口文件
根据命令行参数决定运行哪个模块
"""

import sys
import os

def main():
    """主入口函数"""
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        
        if module_name == "api_server":
            # 运行 API 服务器
            try:
                import api_server
                # 移除第一个参数，让 api_server 正常处理剩余参数
                sys.argv = [sys.argv[0]] + sys.argv[2:]
                if hasattr(api_server, 'main'):
                    api_server.main()
                else:
                    # 如果 api_server.py 没有 main 函数，直接导入执行
                    print("API Server starting...")
            except Exception as e:
                print(f"Error starting API server: {e}")
                sys.exit(1)
                
        elif module_name == "id_updater":
            # 运行 ID 更新器
            try:
                import id_updater
                sys.argv = [sys.argv[0]] + sys.argv[2:]
                if hasattr(id_updater, 'main'):
                    id_updater.main()
                else:
                    # 如果 id_updater.py 没有 main 函数，直接导入执行
                    print("ID Updater starting...")
            except Exception as e:
                print(f"Error starting ID updater: {e}")
                sys.exit(1)
                
        elif module_name == "model_updater":
            # 运行模型更新器
            try:
                import model_updater
                sys.argv = [sys.argv[0]] + sys.argv[2:]
                if hasattr(model_updater, 'main'):
                    model_updater.main()
                else:
                    print("Model Updater starting...")
            except Exception as e:
                print(f"Error starting Model updater: {e}")
                sys.exit(1)
                
        else:
            print(f"Unknown module: {module_name}")
            print("Available modules: api_server, id_updater, model_updater")
            sys.exit(1)
    else:
        # 默认启动 GUI
        try:
            from lmarena_manager import LMArenaManager
            app = LMArenaManager()
            app.run()
        except Exception as e:
            print(f"Error starting GUI: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()
