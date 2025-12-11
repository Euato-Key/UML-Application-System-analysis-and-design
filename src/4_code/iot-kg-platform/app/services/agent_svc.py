from typing import List, Dict, Any, Optional
from app.infra.graph_db import GraphRepository
from app.infra.llm_client import LLMClient


class AgentService:
    """
    智能体服务
    实现智能问答功能
    Trace: [UC-04]
    """
    
    def __init__(self, graph_repo: GraphRepository, llm_client: LLMClient):
        """
        初始化智能体服务
        Trace: [UC-04]
        
        Args:
            graph_repo: 图数据库仓库实例
            llm_client: 大模型客户端实例
        """
        self.graph_repo = graph_repo
        self.llm_client = llm_client
    
    def parse_natural_language(self, question: str) -> str:
        """
        将自然语言问题解析为Cypher查询
        Trace: [UC-04]
        
        Args:
            question: 自然语言问题
        
        Returns:
            生成的Cypher查询
        """
        # 图谱模式信息
        schema_info = """
        知识图谱模式:
        - Node: Device (device_id, name, status, firmware_version, certificate_id)
          - 子节点: Sensor (accuracy, unit)
          - 子节点: Gateway (max_connections, protocol_type)
        - Node: Space (space_id, name, space_type, parent_id)
        - Node: FirmwarePackage (version, download_url, md5, release_time)
        - Node: SecurityAlert (alert_id, level, timestamp, raw_message)
        
        关系:
        - Device-[:LOCATED_IN]->Space
        - Sensor-[:MANAGED_BY]->Gateway
        - Device-[:INSTALLS]->FirmwarePackage
        - Device-[:TRIGGERS]->SecurityAlert
        - Space-[:CONTAINS]->Space
        """
        
        # 构建提示词
        prompt = f"""
        你是一位知识图谱专家，请将用户的自然语言问题转换为Cypher查询语句。
        请严格按照以下要求生成查询：
        1. 只输出Cypher查询，不包含任何解释或其他内容
        2. 使用上述提供的图谱模式
        3. 确保查询语法正确
        4. 使用参数化查询防止注入攻击
        5. 只查询必要的属性
        6. 确保查询语义与用户问题一致
        
        用户问题：{question}
        """
        
        # 调用大模型生成Cypher
        cypher = self.llm_client.chat_completion(prompt)
        
        return cypher
    
    def sanitize_cypher(self, cypher: str) -> str:
        """
        安全过滤Cypher查询，防止注入攻击
        Trace: [UC-04]
        
        Args:
            cypher: 原始Cypher查询
        
        Returns:
            过滤后的安全Cypher查询
        """
        # 简单的安全过滤示例
        # 实际项目中应使用更严格的安全检查
        forbidden_keywords = ["DROP", "DELETE", "CREATE", "MERGE", "SET", "REMOVE", "ALTER"]
        
        # 只允许查询操作
        cypher_lower = cypher.lower()
        for keyword in forbidden_keywords:
            if keyword.lower() in cypher_lower:
                raise ValueError(f"禁止使用的Cypher关键字: {keyword}")
        
        return cypher
    
    def summarize_results(self, question: str, graph_data: List[Dict[str, Any]]) -> str:
        """
        总结图谱查询结果
        Trace: [UC-04]
        
        Args:
            question: 用户原始问题
            graph_data: 图谱查询结果
        
        Returns:
            总结后的文本
        """
        # 构建总结提示词
        prompt = f"""
        请基于以下图谱查询结果，用自然、简洁的语言回答用户的问题。
        回答应直接针对用户问题，避免冗余信息。
        
        用户问题：{question}
        
        查询结果：{graph_data}
        
        请提供清晰、专业的回答：
        """
        
        # 调用大模型生成总结
        summary = self.llm_client.chat_completion(prompt)
        
        return summary
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        智能问答主流程
        Trace: [UC-04]
        
        Args:
            question: 自然语言问题
        
        Returns:
            问答结果，包含文本回答和子图数据
        """
        try:
            # 阶段1：意图识别与Cypher生成
            cypher = self.parse_natural_language(question)
            print(f"生成的Cypher: {cypher}")
            
            # 阶段2：执行图谱查询
            # 安全过滤（仅允许查询操作）
            safe_cypher = self.sanitize_cypher(cypher)
            
            # 执行查询
            graph_data = self.graph_repo.execute_cypher(safe_cypher)
            
            if not graph_data:
                return {
                    "success": True,
                    "answer": "未找到相关信息",
                    "subgraph": []
                }
            
            # 阶段3：结果生成与可视化
            summary = self.summarize_results(question, graph_data)
            
            # 提取子图节点用于可视化
            subgraph_nodes = []
            for record in graph_data:
                for key, value in record.items():
                    if isinstance(value, dict) and "labels" in value:
                        # 提取节点信息
                        node = {
                            "id": value.get("device_id") or value.get("space_id") or value.get("alert_id"),
                            "labels": list(value["labels"]),
                            "properties": value
                        }
                        subgraph_nodes.append(node)
            
            return {
                "success": True,
                "answer": summary,
                "subgraph": subgraph_nodes
            }
            
        except ValueError as e:
            # 安全过滤失败
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            # 其他错误
            print(f"智能问答失败: {e}")
            return {
                "success": False,
                "error": "智能问答服务暂时不可用，请稍后再试"
            }
