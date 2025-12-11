from typing import Dict, Any, Optional
import time
from app.domain.models import Device
from app.infra.mqtt_client import IoTConnector
from app.infra.graph_db import GraphRepository


class LifecycleService:
    """
    生命周期服务
    管理设备的全生命周期
    Trace: [UC-01, UC-06, UC-07]
    """
    
    def __init__(self, iot_connector: IoTConnector, graph_repo: GraphRepository):
        """
        初始化生命周期服务
        Trace: [UC-01, UC-06, UC-07]
        
        Args:
            iot_connector: IoT连接器实例
            graph_repo: 图数据库仓库实例
        """
        self.iot_connector = iot_connector
        self.graph_repo = graph_repo
    
    def register_device(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        注册设备
        Trace: [UC-01]
        
        Args:
            metadata: 设备元数据
        
        Returns:
            注册结果
        """
        try:
            # 1. 生成证书（模拟）
            cert_id = f"cert-{metadata['device_id']}"
            metadata['certificate_id'] = cert_id
            
            # 2. 在图数据库中创建设备节点
            node_type = metadata.get('type', 'Device')
            result = self.graph_repo.merge_node(node_type, metadata)
            
            return {
                "success": True,
                "device_id": metadata['device_id'],
                "certificate_id": cert_id,
                "message": "设备注册成功"
            }
        except Exception as e:
            print(f"设备注册失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def gray_upgrade_firmware(self, version: str, device_ids: list) -> Dict[str, Any]:
        """
        灰度升级固件
        Trace: [UC-06]
        
        Args:
            version: 固件版本
            device_ids: 设备ID列表
        
        Returns:
            升级结果
        """
        try:
            # 1. 验证固件存在
            firmware_query = "MATCH (f:FirmwarePackage {version: $version}) RETURN f"
            firmware_result = self.graph_repo.execute_cypher(firmware_query, {"version": version})
            
            if not firmware_result:
                return {
                    "success": False,
                    "error": f"固件版本 {version} 不存在"
                }
            
            # 2. 升级每个设备
            success_count = 0
            failed_devices = []
            
            for device_id in device_ids:
                # 检查设备是否存在
                device_query = "MATCH (d:Device {device_id: $device_id}) RETURN d"
                device_result = self.graph_repo.execute_cypher(device_query, {"device_id": device_id})
                
                if device_result:
                    # 更新固件信息
                    update_query = """
                    MATCH (d:Device {device_id: $device_id})
                    MATCH (f:FirmwarePackage {version: $version})
                    MERGE (d)-[:INSTALLS]->(f)
                    SET d.firmware_version = $version
                    """
                    self.graph_repo.execute_cypher(update_query, {"device_id": device_id, "version": version})
                    
                    # 发送升级命令
                    topic = f"devices/{device_id}/commands"
                    payload = {
                        "command": "upgrade_firmware",
                        "version": version,
                        "timestamp": time.time()
                    }
                    
                    self.iot_connector.send_mqtt_message(topic, payload)
                    success_count += 1
                else:
                    failed_devices.append(device_id)
            
            return {
                "success": True,
                "total_devices": len(device_ids),
                "success_count": success_count,
                "failed_devices": failed_devices,
                "message": f"灰度升级完成，成功升级 {success_count} 台设备"
            }
        except Exception as e:
            print(f"固件升级失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def log_audit(self, message: str) -> None:
        """
        记录审计日志
        Trace: [UC-07]
        
        Args:
            message: 日志消息
        """
        print(f"[AUDIT] {time.strftime('%Y-%m-%d %H:%M:%S')} - {message}")
    
    def wipe_device_data(self, device_id: str) -> bool:
        """
        擦除设备数据
        Trace: [UC-07]
        
        Args:
            device_id: 设备ID
        
        Returns:
            是否擦除成功
        """
        # 发送擦除命令
        topic = f"devices/{device_id}/commands"
        payload = {
            "command": "WIPE_DATA",
            "timestamp": time.time()
        }
        
        if self.iot_connector.send_mqtt_message(topic, payload):
            # 轮询直到完成（最多3次）
            for _ in range(3):
                time.sleep(1)  # 模拟等待
                # 检查命令执行结果
                result = self.iot_connector.get_command_result(device_id, "WIPE_DATA")
                if result.get("status") == "COMPLETED":
                    return True
        
        return False
    
    def decommission_device(self, device_id: str) -> Dict[str, Any]:
        """
        退役设备
        Trace: [UC-07]
        
        Args:
            device_id: 设备ID
        
        Returns:
            退役结果
        """
        try:
            # 步骤1：检查设备是否存在
            device_query = "MATCH (d:Device {device_id: $device_id}) RETURN d"
            device_result = self.graph_repo.execute_cypher(device_query, {"device_id": device_id})
            
            if not device_result:
                return {
                    "success": False,
                    "error": f"设备 {device_id} 不存在"
                }
            
            device = device_result[0]["d"]
            cert_id = device.get("certificate_id")
            
            # 步骤2：检查在线状态
            is_online = self.iot_connector.check_status(device_id)
            
            if is_online:
                # 步骤3：物理擦除数据
                if not self.wipe_device_data(device_id):
                    return {
                        "success": False,
                        "error": "设备数据擦除失败"
                    }
            else:
                # 设备离线，记录强制退役日志
                self.log_audit(f"设备 {device_id} 离线，执行强制退役")
            
            # 步骤4：撤销证书
            if cert_id:
                self.iot_connector.revoke_certificate(cert_id)
            
            # 步骤5：清理图谱
            # 1. 删除所有关系
            # 2. 设置设备状态为退役
            tx_queries = [
                "MATCH (d:Device {device_id: $device_id})-[r]-() DELETE r",
                "MATCH (d:Device {device_id: $device_id}) SET d.status = 'RETIRED'"
            ]
            
            tx_params = [
                {"device_id": device_id},
                {"device_id": device_id}
            ]
            
            if self.graph_repo.execute_transaction(tx_queries, tx_params):
                return {
                    "success": True,
                    "message": "设备已安全退役"
                }
            else:
                return {
                    "success": False,
                    "error": "图谱清理失败"
                }
                
        except Exception as e:
            print(f"设备退役失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
