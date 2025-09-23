#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
授权码生成工具 - 管理员使用
用于根据用户提供的机器码生成对应的授权码
"""

import sys
import os
from auth_system import AuthSystem


def print_banner():
    """打印程序横幅"""
    print("=" * 60)
    print("LMArenaBridge 授权码生成工具 v1.0")
    print("=" * 60)
    print()


def main():
    print_banner()
    
    # 创建授权系统实例
    auth = AuthSystem()
    
    while True:
        print("\n请选择操作:")
        print("1. 生成授权码")
        print("2. 验证授权码")
        print("3. 批量生成授权码")
        print("4. 查看当前机器的机器码")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == '1':
            # 生成单个授权码
            print("\n--- 生成授权码 ---")
            machine_code = input("请输入用户的机器码: ").strip()
            
            if not machine_code:
                print("错误：机器码不能为空！")
                continue
                
            # 验证机器码格式
            if len(machine_code.replace('-', '')) != 16:
                print("错误：机器码格式不正确！应为 XXXX-XXXX-XXXX-XXXX 格式")
                continue
                
            auth_code = auth.generate_auth_code(machine_code)
            print(f"\n生成成功！")
            print(f"机器码: {machine_code}")
            print(f"授权码: {auth_code}")
            print("\n请将授权码发送给用户。")
            
        elif choice == '2':
            # 验证授权码
            print("\n--- 验证授权码 ---")
            machine_code = input("请输入机器码: ").strip()
            auth_code = input("请输入授权码: ").strip()
            
            if not machine_code or not auth_code:
                print("错误：机器码和授权码不能为空！")
                continue
                
            if auth.verify_auth_code(machine_code, auth_code):
                print("\n✓ 验证成功！授权码有效。")
            else:
                print("\n✗ 验证失败！授权码无效。")
                
        elif choice == '3':
            # 批量生成授权码
            print("\n--- 批量生成授权码 ---")
            print("请输入机器码列表（每行一个机器码，输入空行结束）:")
            
            machine_codes = []
            while True:
                code = input().strip()
                if not code:
                    break
                if len(code.replace('-', '')) == 16:
                    machine_codes.append(code)
                else:
                    print(f"警告：忽略无效的机器码 '{code}'")
                    
            if machine_codes:
                print(f"\n共 {len(machine_codes)} 个机器码，正在生成授权码...")
                print("\n" + "=" * 60)
                
                # 生成结果文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"auth_codes_{timestamp}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("LMArenaBridge 授权码列表\n")
                    f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    for i, machine_code in enumerate(machine_codes, 1):
                        auth_code = auth.generate_auth_code(machine_code)
                        print(f"{i}. 机器码: {machine_code}")
                        print(f"   授权码: {auth_code}")
                        print()
                        
                        f.write(f"用户 {i}:\n")
                        f.write(f"机器码: {machine_code}\n")
                        f.write(f"授权码: {auth_code}\n")
                        f.write("-" * 40 + "\n\n")
                        
                print("=" * 60)
                print(f"\n批量生成完成！结果已保存到: {filename}")
            else:
                print("没有有效的机器码。")
                
        elif choice == '4':
            # 查看当前机器的机器码
            print("\n--- 当前机器信息 ---")
            print(f"操作系统: {platform.system()} {platform.release()}")
            print(f"机器码: {auth.get_machine_code()}")
            
        elif choice == '5':
            # 退出
            print("\n感谢使用！再见。")
            break
            
        else:
            print("\n无效的选项，请重新选择。")
            
        input("\n按回车键继续...")


if __name__ == "__main__":
    # 添加必要的导入
    from datetime import datetime
    import platform
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)
