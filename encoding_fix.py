#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码修复脚本
用于解决Windows环境下的编码问题
"""

import sys
import os
import locale
import codecs

def fix_encoding():
    """修复Python环境的编码问题"""
    # 强制设置UTF-8编码
    if sys.platform == "win32":
        # 设置环境变量
        os.environ["PYTHONUTF8"] = "1"
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 尝试设置控制台代码页为UTF-8
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # 设置控制台输出代码页为UTF-8
            kernel32.SetConsoleOutputCP(65001)
            # 设置控制台输入代码页为UTF-8
            kernel32.SetConsoleCP(65001)
        except:
            pass
        
        # 重定向标准输出和错误输出
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        
        # 设置默认编码
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')

# 在导入其他模块之前修复编码
fix_encoding()

# 现在导入并运行主程序
if __name__ == "__main__":
    # 导入main模块的功能
    import main
    # 调用main模块的主函数
    main.main()
