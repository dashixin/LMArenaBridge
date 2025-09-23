#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一机一码授权系统核心模块
用于生成机器码、验证授权码、管理授权状态
"""

import hashlib
import hmac
import base64
import json
import os
import platform
import subprocess
import re
from datetime import datetime
from cryptography.fernet import Fernet


class AuthSystem:
    def __init__(self):
        self.auth_file = ".auth"
        self.fernet_key = b'aK3xY9zB5mN8qW2eR6tY1uI4oP7sD0fG3hJ6kL9cV2b='  # 用于加密存储
        self.cipher = Fernet(self.fernet_key)
        
    def get_machine_code(self):
        """获取机器码 - 简化版本，只使用MAC地址"""
        import uuid
        
        # 获取MAC地址
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                      for ele in range(0,8*6,8)][::-1])
        
        # 添加主机名增加唯一性
        hostname = platform.node()
        
        # 组合信息
        hardware_info = [mac, hostname]
            
        # 生成机器码
        hardware_string = '|'.join(hardware_info)
        machine_code_hash = hashlib.sha256(hardware_string.encode()).hexdigest()
        
        # 返回前16位，格式化为 XXXX-XXXX-XXXX-XXXX
        machine_code = machine_code_hash[:16].upper()
        formatted_code = '-'.join([machine_code[i:i+4] for i in range(0, 16, 4)])
        
        return formatted_code
        
    def verify_auth_code(self, machine_code, auth_code):
        """验证授权码"""
        # 这里只是简单的格式验证，实际验证逻辑应该更复杂
        # 客户端不应该包含生成授权码的逻辑
        if not auth_code or not machine_code:
            return False
        
        # 验证格式：XXXX-XXXX-XXXX-XXXX
        import re
        pattern = r'^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$'
        return bool(re.match(pattern, auth_code.upper()))
        
    def save_auth_info(self, auth_code):
        """保存授权信息"""
        auth_data = {
            'auth_code': auth_code,
            'machine_code': self.get_machine_code(),
            'auth_date': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # 加密数据
        json_data = json.dumps(auth_data)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        
        # 保存到文件
        with open(self.auth_file, 'wb') as f:
            f.write(encrypted_data)
            
    def load_auth_info(self):
        """加载授权信息"""
        if not os.path.exists(self.auth_file):
            return None
            
        try:
            with open(self.auth_file, 'rb') as f:
                encrypted_data = f.read()
                
            # 解密数据
            decrypted_data = self.cipher.decrypt(encrypted_data)
            auth_data = json.loads(decrypted_data.decode())
            
            return auth_data
            
        except Exception as e:
            print(f"加载授权信息失败: {e}")
            return None
            
    def is_authorized(self):
        """检查是否已授权"""
        auth_info = self.load_auth_info()
        if not auth_info:
            return False
            
        # 获取当前机器码
        current_machine_code = self.get_machine_code()
        
        # 验证机器码是否匹配
        if auth_info.get('machine_code') != current_machine_code:
            return False
            
        # 验证授权码
        return self.verify_auth_code(current_machine_code, auth_info.get('auth_code', ''))
        
    def get_auth_status(self):
        """获取授权状态详情"""
        auth_info = self.load_auth_info()
        current_machine_code = self.get_machine_code()
        
        if not auth_info:
            return {
                'authorized': False,
                'reason': '未找到授权文件',
                'machine_code': current_machine_code
            }
            
        if auth_info.get('machine_code') != current_machine_code:
            return {
                'authorized': False,
                'reason': '机器码不匹配',
                'machine_code': current_machine_code,
                'saved_machine_code': auth_info.get('machine_code')
            }
            
        if not self.verify_auth_code(current_machine_code, auth_info.get('auth_code', '')):
            return {
                'authorized': False,
                'reason': '授权码无效',
                'machine_code': current_machine_code
            }
            
        return {
            'authorized': True,
            'machine_code': current_machine_code,
            'auth_date': auth_info.get('auth_date'),
            'version': auth_info.get('version')
        }


# 测试代码
if __name__ == "__main__":
    auth = AuthSystem()
    
    print("=== 授权系统测试 ===")
    print(f"当前系统: {platform.system()}")
    print(f"机器码: {auth.get_machine_code()}")
    
    # 测试授权状态
    status = auth.get_auth_status()
    print(f"授权状态: {status}")
