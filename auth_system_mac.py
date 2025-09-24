#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac版授权系统
使用macOS特定的硬件信息生成机器码
"""

import subprocess
import hashlib
import platform
import uuid


def get_mac_serial_number():
    """获取Mac的序列号"""
    try:
        # 使用 system_profiler 获取硬件信息
        cmd = "system_profiler SPHardwareDataType | grep 'Serial Number' | awk '{print $4}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        serial = result.stdout.strip()
        if serial:
            return serial
    except:
        pass
    
    # 备用方案：使用 ioreg
    try:
        cmd = "ioreg -l | grep IOPlatformSerialNumber | awk '{print $4}' | sed 's/\"//g'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        serial = result.stdout.strip()
        if serial:
            return serial
    except:
        pass
    
    return None


def get_mac_uuid():
    """获取Mac的硬件UUID"""
    try:
        cmd = "system_profiler SPHardwareDataType | grep 'Hardware UUID' | awk '{print $3}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        hw_uuid = result.stdout.strip()
        if hw_uuid:
            return hw_uuid
    except:
        pass
    
    # 备用方案
    try:
        cmd = "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID | awk '{print $3}' | sed 's/\"//g'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        hw_uuid = result.stdout.strip()
        if hw_uuid:
            return hw_uuid
    except:
        pass
    
    return None


def get_mac_model():
    """获取Mac型号"""
    try:
        cmd = "system_profiler SPHardwareDataType | grep 'Model Identifier' | awk '{print $3}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        model = result.stdout.strip()
        if model:
            return model
    except:
        pass
    
    return platform.machine()


def get_network_interfaces():
    """获取网络接口信息"""
    interfaces = []
    try:
        # 获取所有网络接口的MAC地址
        cmd = "ifconfig | grep ether | awk '{print $2}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        macs = result.stdout.strip().split('\n')
        interfaces.extend([mac for mac in macs if mac])
    except:
        pass
    
    # 如果没有获取到，使用Python的uuid模块
    if not interfaces:
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) 
                          for ele in range(0,8*6,8)][::-1])
            interfaces.append(mac)
        except:
            pass
    
    return interfaces


def get_mac_machine_code():
    """生成Mac的机器码"""
    components = []
    
    # 1. 序列号
    serial = get_mac_serial_number()
    if serial:
        components.append(f"SN:{serial}")
    
    # 2. 硬件UUID
    hw_uuid = get_mac_uuid()
    if hw_uuid:
        components.append(f"UUID:{hw_uuid}")
    
    # 3. Mac型号
    model = get_mac_model()
    if model:
        components.append(f"MODEL:{model}")
    
    # 4. 网络接口
    interfaces = get_network_interfaces()
    if interfaces:
        # 只使用第一个稳定的MAC地址
        components.append(f"MAC:{interfaces[0]}")
    
    # 如果没有获取到任何硬件信息，使用备用方案
    if not components:
        # 使用Python的uuid模块生成一个基于MAC地址的UUID
        node_id = uuid.getnode()
        components.append(f"NODE:{node_id}")
    
    # 组合所有组件
    combined = "|".join(sorted(components))
    
    # 生成哈希值作为机器码
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    machine_code = hash_obj.hexdigest()[:16].upper()
    
    return machine_code


def test_mac_hardware_info():
    """测试Mac硬件信息获取"""
    print("=== Mac Hardware Information ===")
    print(f"Serial Number: {get_mac_serial_number()}")
    print(f"Hardware UUID: {get_mac_uuid()}")
    print(f"Model: {get_mac_model()}")
    print(f"Network Interfaces: {get_network_interfaces()}")
    print(f"Machine Code: {get_mac_machine_code()}")


if __name__ == "__main__":
    # 测试功能
    test_mac_hardware_info()
