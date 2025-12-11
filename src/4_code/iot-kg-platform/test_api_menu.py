#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物联网设备知识图谱交互管理平台API测试脚本
具有交互式菜单，可选择测试不同的API接口
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"


def print_menu(title, options):
    """打印菜单"""
    print(f"\n{'='*40}")
    print(f"{title:^40}")
    print(f"{'='*40}")
    for i, option in enumerate(options, 1):
        print(f"{i:2d}. {option}")
    print(f"{'='*40}")


def get_user_choice(max_choice):
    """获取用户选择"""
    while True:
        try:
            choice = input(f"请输入选择 (1-{max_choice}): ")
            if choice.lower() == 'q':
                return 'q'
            choice = int(choice)
            if 1 <= choice <= max_choice:
                return choice
            else:
                print(f"无效选择，请输入1-{max_choice}之间的数字")
        except ValueError:
            print("无效输入，请输入数字")


def test_root():
    """测试根路径接口"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_bind_topology():
    """测试绑定拓扑关系接口"""
    try:
        # 获取用户输入
        device_id = input("请输入设备ID: ")
        space_id = input("请输入空间ID: ")
        gateway_id = input("请输入网关ID (可选，直接回车跳过): ")
        
        # 构建请求体
        data = {
            "device_id": device_id,
            "space_id": space_id
        }
        if gateway_id:
            data["gateway_id"] = gateway_id
        
        response = requests.post(f"{BASE_URL}/api/v1/topology/bind", json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_associate_network():
    """测试构建网络关联接口"""
    try:
        # 获取用户输入
        sensor_id = input("请输入传感器ID: ")
        gateway_id = input("请输入网关ID: ")
        
        # 构建请求体
        data = {
            "sensor_id": sensor_id,
            "gateway_id": gateway_id
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/topology/associate", json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_get_impact_range():
    """测试获取设备影响范围接口"""
    try:
        # 获取用户输入
        device_id = input("请输入设备ID: ")
        
        response = requests.get(f"{BASE_URL}/api/v1/topology/impact/{device_id}")
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_ask_question():
    """测试智能问答接口"""
    try:
        # 获取用户输入
        question = input("请输入问题: ")
        
        # 构建请求体
        data = {
            "question": question
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/agent/ask", json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_register_device():
    """测试注册设备接口"""
    try:
        # 获取用户输入
        device_id = input("请输入设备ID: ")
        name = input("请输入设备名称: ")
        device_type = input("请输入设备类型 (Device/Sensor/Gateway，默认为Device): ") or "Device"
        status = input("请输入设备状态 (在线/离线，默认为离线): ") or "离线"
        firmware_version = input("请输入固件版本 (可选): ")
        
        # 构建请求体
        data = {
            "device_id": device_id,
            "name": name,
            "type": device_type,
            "status": status
        }
        
        # 根据设备类型添加额外字段
        if device_type == "Sensor":
            accuracy = input("请输入传感器精度 (可选): ")
            unit = input("请输入传感器单位 (可选): ")
            if accuracy:
                data["accuracy"] = float(accuracy)
            if unit:
                data["unit"] = unit
        elif device_type == "Gateway":
            max_connections = input("请输入最大连接数 (可选): ")
            protocol_type = input("请输入协议类型 (可选): ")
            if max_connections:
                data["max_connections"] = int(max_connections)
            if protocol_type:
                data["protocol_type"] = protocol_type
        
        if firmware_version:
            data["firmware_version"] = firmware_version
        
        response = requests.post(f"{BASE_URL}/api/v1/lifecycle/register", json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_upgrade_firmware():
    """测试灰度升级固件接口"""
    try:
        # 获取用户输入
        version = input("请输入固件版本: ")
        device_ids_str = input("请输入设备ID列表 (逗号分隔): ")
        
        # 解析设备ID列表
        device_ids = [id.strip() for id in device_ids_str.split(",")]
        
        # 构建请求体
        data = {
            "version": version,
            "device_ids": device_ids
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/lifecycle/upgrade", json=data)
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_decommission_device():
    """测试退役设备接口"""
    try:
        # 获取用户输入
        device_id = input("请输入设备ID: ")
        
        response = requests.post(f"{BASE_URL}/api/v1/lifecycle/decommission/{device_id}")
        print(f"\n状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")


def test_all_interfaces():
    """测试所有接口（默认参数）"""
    print("\n开始测试所有接口...")
    
    # 测试基础接口
    print("\n1. 测试根路径接口")
    test_root()
    time.sleep(1)
    
    print("\n2. 测试健康检查接口")
    test_health_check()
    time.sleep(1)
    
    # 测试设备注册（使用默认参数）
    print("\n3. 测试注册设备接口 (使用默认参数)")
    try:
        data = {
            "device_id": "test-sensor-001",
            "name": "测试温度传感器",
            "type": "Sensor",
            "status": "在线",
            "firmware_version": "1.0.0",
            "accuracy": 0.5,
            "unit": "℃"
        }
        response = requests.post(f"{BASE_URL}/api/v1/lifecycle/register", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")
    time.sleep(1)
    
    # 测试绑定拓扑关系（使用默认参数）
    print("\n4. 测试绑定拓扑关系接口 (使用默认参数)")
    try:
        data = {
            "device_id": "test-sensor-001",
            "space_id": "test-room-001",
            "gateway_id": "test-gateway-001"
        }
        response = requests.post(f"{BASE_URL}/api/v1/topology/bind", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")
    time.sleep(1)
    
    # 测试智能问答（使用默认参数）
    print("\n5. 测试智能问答接口 (使用默认参数)")
    try:
        data = {
            "question": "设备test-sensor-001连接到哪个网关？"
        }
        response = requests.post(f"{BASE_URL}/api/v1/agent/ask", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"测试失败: {e}")
    
    print("\n所有接口测试完成！")


def main_menu():
    """主菜单"""
    while True:
        main_options = [
            "测试基础接口",
            "测试拓扑管理接口",
            "测试智能问答接口",
            "测试设备生命周期接口",
            "测试所有接口（默认参数）",
            "退出测试"
        ]
        
        print_menu("主菜单", main_options)
        choice = get_user_choice(len(main_options))
        
        if choice == 1:
            # 测试基础接口
            while True:
                base_options = [
                    "测试根路径接口",
                    "测试健康检查接口",
                    "返回主菜单"
                ]
                
                print_menu("基础接口测试", base_options)
                base_choice = get_user_choice(len(base_options))
                
                if base_choice == 1:
                    test_root()
                elif base_choice == 2:
                    test_health_check()
                elif base_choice == 3:
                    break
        
        elif choice == 2:
            # 测试拓扑管理接口
            while True:
                topology_options = [
                    "测试绑定拓扑关系",
                    "测试构建网络关联",
                    "测试获取设备影响范围",
                    "返回主菜单"
                ]
                
                print_menu("拓扑管理接口测试", topology_options)
                topology_choice = get_user_choice(len(topology_options))
                
                if topology_choice == 1:
                    test_bind_topology()
                elif topology_choice == 2:
                    test_associate_network()
                elif topology_choice == 3:
                    test_get_impact_range()
                elif topology_choice == 4:
                    break
        
        elif choice == 3:
            # 测试智能问答接口
            test_ask_question()
        
        elif choice == 4:
            # 测试设备生命周期接口
            while True:
                lifecycle_options = [
                    "测试注册设备",
                    "测试灰度升级固件",
                    "测试退役设备",
                    "返回主菜单"
                ]
                
                print_menu("设备生命周期接口测试", lifecycle_options)
                lifecycle_choice = get_user_choice(len(lifecycle_options))
                
                if lifecycle_choice == 1:
                    test_register_device()
                elif lifecycle_choice == 2:
                    test_upgrade_firmware()
                elif lifecycle_choice == 3:
                    test_decommission_device()
                elif lifecycle_choice == 4:
                    break
        
        elif choice == 5:
            # 测试所有接口
            test_all_interfaces()
        
        elif choice == 6:
            # 退出测试
            print("\n感谢使用API测试脚本！")
            break


if __name__ == "__main__":
    print("="*60)
    print("物联网设备知识图谱交互管理平台API测试脚本")
    print("="*60)
    print(f"API基础URL: {BASE_URL}")
    print("请确保API服务正在运行...")
    
    # 检查API服务是否可用
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API服务已成功连接！")
            main_menu()
        else:
            print(f"✗ 无法连接到API服务，状态码: {response.status_code}")
            print("请确保API服务正在运行，然后重试。")
    except Exception as e:
        print(f"✗ 无法连接到API服务: {e}")
        print("请确保API服务正在运行，然后重试。")
