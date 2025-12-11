from typing import List, Dict, Any, Optional
from app.domain.models import Device, Space
from app.infra.graph_db import GraphRepository


class TopologyService:
    """
    拓扑服务
    处理设备与空间的拓扑关系
    Trace: [UC-02]
    """
    
    def __init__(self, graph_repo: GraphRepository):
        """
        初始化拓扑服务
        Trace: [UC-02]
        
        Args:
            graph_repo: 图数据库仓库实例
        """
        self.graph_repo = graph_repo
    
    def validate_logic(self, device_id: str, space_id: str, gateway_id: Optional[str] = None) -> bool:
        """
        校验拓扑配置逻辑
        Trace: [UC-02]
        
        Args:
            device_id: 设备ID
            space_id: 空间ID
            gateway_id: 可选的网关ID
        
        Returns:
            是否校验通过
        """
        # 1. 校验设备是否存在
        device_query = "MATCH (d:Device {device_id: $device_id}) RETURN d"
        device_result = self.graph_repo.execute_cypher(device_query, {"device_id": device_id})
        if not device_result:
            print(f"设备不存在: {device_id}")
            return False
        
        # 2. 校验空间是否存在
        space_query = "MATCH (s:Space {space_id: $space_id}) RETURN s"
        space_result = self.graph_repo.execute_cypher(space_query, {"space_id": space_id})
        if not space_result:
            print(f"空间不存在: {space_id}")
            return False
        
        # 3. 如果提供了网关ID，校验网关是否存在且容量是否足够
        if gateway_id:
            gateway_query = "MATCH (g:Gateway {device_id: $gateway_id}) RETURN g, count((g)-[:MANAGES]->()) as connected_count"
            gateway_result = self.graph_repo.execute_cypher(gateway_query, {"gateway_id": gateway_id})
            if not gateway_result:
                print(f"网关不存在: {gateway_id}")
                return False
            
            gateway = gateway_result[0]["g"]
            connected_count = gateway_result[0]["connected_count"]
            
            if connected_count >= gateway.get("max_connections", 100):
                print(f"网关 {gateway_id} 已达到最大连接数")
                return False
        
        return True
    
    def update_device_location(self, device_id: str, space_id: str) -> bool:
        """
        更新设备位置
        Trace: [UC-02]
        
        Args:
            device_id: 设备ID
            space_id: 空间ID
        
        Returns:
            是否更新成功
        """
        try:
            # 更新设备所在空间关系
            query = """
            MATCH (d:Device {device_id: $device_id})
            OPTIONAL MATCH (d)-[r:LOCATED_IN]->()
            DELETE r
            WITH d
            MATCH (s:Space {space_id: $space_id})
            MERGE (d)-[:LOCATED_IN]->(s)
            RETURN count(d) as updated_count
            """
            
            result = self.graph_repo.execute_cypher(query, {"device_id": device_id, "space_id": space_id})
            return result[0]["updated_count"] > 0
        except Exception as e:
            print(f"更新设备位置失败: {e}")
            return False
    
    def build_merge_cypher(self, device_id: str, space_id: str, gateway_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        构建用于合并拓扑关系的Cypher语句
        Trace: [UC-02]
        
        Args:
            device_id: 设备ID
            space_id: 空间ID
            gateway_id: 可选的网关ID
        
        Returns:
            Cypher查询和参数的列表
        """
        queries = []
        
        # 1. 设备与空间的关系
        location_query = """
        MATCH (d:Device {device_id: $device_id})
        MATCH (s:Space {space_id: $space_id})
        MERGE (d)-[:LOCATED_IN]->(s)
        """
        queries.append({
            "query": location_query,
            "params": {"device_id": device_id, "space_id": space_id}
        })
        
        # 2. 设备与网关的关系（如果提供了网关）
        if gateway_id:
            gateway_query = """
            MATCH (d:Device {device_id: $device_id})
            MATCH (g:Gateway {device_id: $gateway_id})
            MERGE (d)-[:CONNECTED_TO]->(g)
            """
            queries.append({
                "query": gateway_query,
                "params": {"device_id": device_id, "gateway_id": gateway_id}
            })
        
        return queries
    
    def bind_topology(self, device_id: str, space_id: str, gateway_id: Optional[str] = None) -> Dict[str, Any]:
        """
        绑定拓扑关系
        Trace: [UC-02]
        
        Args:
            device_id: 设备ID
            space_id: 空间ID
            gateway_id: 可选的网关ID
        
        Returns:
            绑定结果
        """
        # 步骤1：业务校验
        if not self.validate_logic(device_id, space_id, gateway_id):
            return {"success": False, "message": "拓扑配置校验失败"}
        
        # 步骤2：实体状态更新
        if not self.update_device_location(device_id, space_id):
            return {"success": False, "message": "更新设备位置失败"}
        
        # 步骤3：构建Cypher并执行
        cypher_queries = self.build_merge_cypher(device_id, space_id, gateway_id)
        
        nodes_created = 0
        rels_created = 0
        
        for cypher in cypher_queries:
            result = self.graph_repo.execute_cypher(cypher["query"], cypher["params"])
            # 统计结果（这里简化处理）
            rels_created += 1
        
        return {
            "success": True,
            "message": "拓扑关系已建立",
            "nodes_created": nodes_created,
            "rels_created": rels_created
        }
    
    def build_network_association(self, sensor_id: str, gateway_id: str) -> Dict[str, Any]:
        """
        构建传感器与网关的网络关联
        Trace: [UC-02]
        
        Args:
            sensor_id: 传感器ID
            gateway_id: 网关ID
        
        Returns:
            关联结果
        """
        # 校验传感器和网关是否存在
        sensor_query = "MATCH (s:Sensor {device_id: $sensor_id}) RETURN s"
        sensor_result = self.graph_repo.execute_cypher(sensor_query, {"sensor_id": sensor_id})
        
        gateway_query = "MATCH (g:Gateway {device_id: $gateway_id}) RETURN g, count((g)-[:MANAGES]->()) as connected_count"
        gateway_result = self.graph_repo.execute_cypher(gateway_query, {"gateway_id": gateway_id})
        
        if not sensor_result:
            return {"success": False, "message": "传感器不存在"}
        
        if not gateway_result:
            return {"success": False, "message": "网关不存在"}
        
        # 校验网关容量
        gateway = gateway_result[0]["g"]
        connected_count = gateway_result[0]["connected_count"]
        
        if connected_count >= gateway.get("max_connections", 100):
            return {"success": False, "message": "网关已达到最大连接数"}
        
        # 创建关联关系
        query = """
        MATCH (s:Sensor {device_id: $sensor_id})
        MATCH (g:Gateway {device_id: $gateway_id})
        MERGE (s)-[:MANAGED_BY]->(g)
        RETURN count(s) as updated_count
        """
        
        result = self.graph_repo.execute_cypher(query, {"sensor_id": sensor_id, "gateway_id": gateway_id})
        
        return {
            "success": True,
            "message": "网络关联已建立",
            "updated_count": result[0]["updated_count"]
        }
    
    def get_impact_range(self, device_id: str) -> List[Dict[str, Any]]:
        """
        获取设备影响范围
        Trace: [UC-02]
        
        Args:
            device_id: 设备ID
        
        Returns:
            影响范围内的设备列表
        """
        query = """
        MATCH (d:Device {device_id: $device_id})-[:CONNECTED_TO*1..2]-(related:Device)
        WHERE related.device_id <> $device_id
        RETURN related
        """
        
        result = self.graph_repo.execute_cypher(query, {"device_id": device_id})
        return [record["related"] for record in result]
