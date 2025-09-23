#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
授权码生成模块
用于生成授权码的管理端操作
"""

import hmac
import hashlib
import base64

class AuthKeyGen:
    def __init__(self, secret_key):
        if isinstance(secret_key, str):
            self.secret_key = secret_key.encode()
        else:
            self.secret_key = secret_key

    def generate_auth_code(self, machine_code):
        """生成授权码"""
        # 移除机器码中的连字符
        clean_machine_code = machine_code.replace('-', '')
        
        # 使用HMAC-SHA256生成授权码
        auth_hash = hmac.new(
            self.secret_key,
            clean_machine_code.encode(),
            hashlib.sha256
        ).digest()
        
        # 使用Base32编码（去掉填充字符）
        auth_code_raw = base64.b32encode(auth_hash)[:16].decode('utf-8')
        
        # 格式化为 XXXX-XXXX-XXXX-XXXX
        formatted_code = '-'.join([auth_code_raw[i:i+4] for i in range(0, 16, 4)])
        
        return formatted_code

# 示例用法
if __name__ == "__main__":
    # 使用正确的密钥 - 必须与 lmarena_manager.py 中的密钥一致
    keygen = AuthKeyGen(b"LMArena_Bridge_2024_Secret_Key_Do_Not_Share")
    machine_code = "D912-73BF-3F5C-8B64"  # 替换为实际机器码
    auth_code = keygen.generate_auth_code(machine_code)
    print(f"生成的授权码: {auth_code}")
