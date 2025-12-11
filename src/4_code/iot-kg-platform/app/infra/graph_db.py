from neo4j import GraphDatabase, basic_auth
from typing import Dict, Any, Optional, List


class GraphRepository:
    """
    图数据库仓库接口实现
    Trace: [UC-02, UC-04, UC-07]
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        初始化Neo4j驱动连接
        Trace: [UC-02, UC-04, UC-07]
        """
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行Cypher查询
        Trace: [UC-02, UC-04, UC-07]
        
        Args:
            query: Cypher查询语句
            parameters: 查询参数
        
        Returns:
            查询结果列表
        """
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
    
    def merge_node(self, label: str, props: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并节点（如果存在则更新，不存在则创建）
        Trace: [UC-02]
        
        Args:
            label: 节点标签
            props: 节点属性，必须包含唯一标识属性
        
        Returns:
            操作后的节点数据
        """
        # 构建MERGE语句
        unique_key = next(iter(props.keys()))  # 假设第一个属性为唯一标识
        query = f"""
        MERGE (n:{label} {{ {unique_key}: ${unique_key} }})
        SET n += $props
        RETURN n
        """
        
        parameters = {unique_key: props[unique_key], "props": props}
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return result.single()['n']
    
    def delete_relationship(self, from_node: Dict[str, Any], to_node: Dict[str, Any], relationship_type: str) -> bool:
        """
        删除节点之间的关系
        Trace: [UC-07]
        
        Args:
            from_node: 起始节点信息（label和唯一标识）
            to_node: 目标节点信息（label和唯一标识）
            relationship_type: 关系类型
        
        Returns:
            是否删除成功
        """
        from_label = from_node['label']
        from_key = next(iter(from_node['props'].keys()))
        from_value = from_node['props'][from_key]
        
        to_label = to_node['label']
        to_key = next(iter(to_node['props'].keys()))
        to_value = to_node['props'][to_key]
        
        query = f"""
        MATCH (a:{from_label} {{ {from_key}: ${from_key} }})-[r:{relationship_type}]->(b:{to_label} {{ {to_key}: ${to_key} }})
        DELETE r
        RETURN count(r) as deleted_count
        """
        
        parameters = {
            from_key: from_value,
            to_key: to_value
        }
        
        with self.driver.session() as session:
            result = session.run(query, parameters)
            deleted_count = result.single()['deleted_count']
            return deleted_count > 0
    
    def execute_transaction(self, queries: List[str], parameters_list: List[Optional[Dict[str, Any]]]) -> bool:
        """
        执行事务
        Trace: [UC-07]
        
        Args:
            queries: Cypher查询列表
            parameters_list: 查询参数列表
        
        Returns:
            事务是否提交成功
        """
        try:
            with self.driver.session() as session:
                def transaction_work(tx):
                    for i, query in enumerate(queries):
                        params = parameters_list[i] if i < len(parameters_list) else None
                        tx.run(query, params)
                
                session.execute_write(transaction_work)
                return True
        except Exception as e:
            print(f"事务执行失败: {e}")
            return False
    
    def close(self):
        """
        关闭数据库连接
        Trace: [UC-02, UC-04, UC-07]
        """
        if self.driver:
            self.driver.close()
