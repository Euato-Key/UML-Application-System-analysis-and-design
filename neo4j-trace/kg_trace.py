#!/usr/bin/env python3
"""
知识图谱反向追踪脚本
用于扫描代码文件，建立代码与类之间的关系
"""

import argparse
import os
import re
import json
from typing import List, Dict, Tuple, Optional
from neo4j import GraphDatabase


class CodeScanner:
    """
    代码扫描器
    """
    
    def __init__(self):
        """
        初始化扫描器
        """
        self.class_pattern = r'class\s+([\w]+)\s*\(.*\):'
        self.trace_pattern = r'Trace:\s*\[(.*?)\]'
        self.file_extensions = ['.py']
    
    def scan_file(self, file_path: str) -> List[Dict]:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件中的类和追踪信息
        """
        classes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 改进类定义匹配逻辑，支持更多格式
            # 先找到所有类定义
            class_def_pattern = r'class\s+([\w]+)\s*\([^)]*\):'
            class_defs = re.finditer(class_def_pattern, content)
            
            for class_def in class_defs:
                class_name = class_def.group(1)
                class_start = class_def.end()
                
                # 在类定义后查找Docstring
                # 计算下一个类定义的位置，限制查找范围
                next_class_match = re.search(class_def_pattern, content[class_start:])
                if next_class_match:
                    next_class_start = class_start + next_class_match.start()
                    class_content = content[class_start:next_class_start]
                else:
                    class_content = content[class_start:]
                
                # 查找双引号Docstring
                docstring_match = re.search(r'\s*"""\s*([\s\S]*?)\s*"""', class_content)
                docstring = ""
                if docstring_match:
                    docstring = docstring_match.group(1)
                else:
                    # 尝试查找单引号Docstring
                    docstring_match = re.search(r"\s*'''\s*([\s\S]*?)\s*'''", class_content)
                    if docstring_match:
                        docstring = docstring_match.group(1)
                
                # 提取追踪标记
                trace_matches = re.findall(self.trace_pattern, docstring)
                traces = []
                for trace_match in trace_matches:
                    # 提取UC编号（支持UC-XX或UCXX格式）
                    uc_matches = re.findall(r'UC[-]?(\d+)', trace_match)
                    traces = [f'UC{uc}' for uc in uc_matches]
                
                classes.append({
                    'name': class_name,
                    'traces': traces
                })
        
        except Exception as e:
            print(f"扫描文件出错 {file_path}: {e}")
        
        return classes
    
    def scan_directory(self, dir_path: str) -> Dict[str, List[Dict]]:
        """
        扫描目录
        
        Args:
            dir_path: 目录路径
            
        Returns:
            文件路径到类列表的映射
        """
        result = {}
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.file_extensions):
                    file_path = os.path.join(root, file)
                    classes = self.scan_file(file_path)
                    if classes:
                        result[file_path] = classes
        
        return result


class Neo4jTracer:
    """
    Neo4j追踪器
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        初始化追踪器
        
        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        """
        关闭数据库连接
        """
        self.driver.close()
    
    def import_code_files(self, code_map: Dict[str, List[Dict]]):
        """
        导入代码文件
        
        Args:
            code_map: 文件路径到类列表的映射
        """
        with self.driver.session() as session:
            for file_path, classes in code_map.items():
                # 创建代码文件节点
                relative_path = os.path.relpath(file_path)
                session.run(
                    "CREATE (f:CodeFile {path: $path, type: 'CodeFile'})",
                    path=relative_path
                )
        print(f"已导入 {len(code_map)} 个代码文件")
    
    def import_implement_relations(self, code_map: Dict[str, List[Dict]]):
        """
        导入实现关系
        
        Args:
            code_map: 文件路径到类列表的映射
        """
        with self.driver.session() as session:
            for file_path, classes in code_map.items():
                relative_path = os.path.relpath(file_path)
                
                for cls in classes:
                    # 创建或更新Class节点
                    session.run(
                        "MERGE (c:Class {name: $class_name, id: $class_id})",
                        class_name=cls['name'], class_id=cls['name']
                    )
                    
                    # 建立代码文件与类的实现关系
                    session.run(
                        "MATCH (f:CodeFile {path: $file_path})"
                        "MATCH (c:Class {name: $class_name})"
                        "MERGE (f)-[:IMPLEMENTS]->(c)",
                        file_path=relative_path, class_name=cls['name']
                    )
        print("已导入实现关系")
    
    def import_code_traces(self, code_map: Dict[str, List[Dict]]):
        """
        导入代码中的追踪关系
        
        Args:
            code_map: 文件路径到类列表的映射
        """
        with self.driver.session() as session:
            for file_path, classes in code_map.items():
                relative_path = os.path.relpath(file_path)
                
                for cls in classes:
                    for trace in cls['traces']:
                        # 建立类与用例的追踪关系
                        session.run(
                            "MATCH (c:Class) WHERE c.name = $class_name OR c.id = $class_name "
                            "MATCH (uc:UseCase {id: $use_case_id})"
                            "MERGE (c)-[:TRACE]->(uc)",
                            class_name=cls['name'], use_case_id=trace
                        )
        print("已导入代码追踪关系")
    
    def verify_connections(self):
        """
        验证连接关系
        """
        with self.driver.session() as session:
            # 检查需求-类-代码的三级关系
            result = session.run(
                "MATCH (uc:UseCase)<-[:TRACE]-(c:Class)<-[:IMPLEMENTS]-(f:CodeFile)"
                "RETURN uc.id, c.name, f.path "
                "LIMIT 10"
            )
            
            print("\n=== 验证连接关系 ===")
            print("需求-类-代码 三级关系示例：")
            count = 0
            for record in result:
                print(f"{record['uc.id']} -> {record['c.name']} -> {record['f.path']}")
                count += 1
            
            if count == 0:
                print("未找到三级关系")
            
            # 统计连接数
            stats = session.run(
                "MATCH (uc:UseCase)"
                "OPTIONAL MATCH (uc)<-[:TRACE]-(c:Class)"
                "OPTIONAL MATCH (c)<-[:IMPLEMENTS]-(f:CodeFile)"
                "RETURN count(DISTINCT uc) as use_cases, count(DISTINCT c) as classes, count(DISTINCT f) as code_files"
            ).single()
            
            print(f"\n统计信息：")
            print(f"用例数: {stats['use_cases']}")
            print(f"类数: {stats['classes']}")
            print(f"代码文件数: {stats['code_files']}")


def load_neo4j_config() -> Dict:
    """
    加载Neo4j配置
    
    Returns:
        配置字典
    """
    config_path = '服务器的neo4j配置.json'
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {
            'uri': config['endpoints']['bolt'],
            'user': config['credentials']['username'],
            'password': config['credentials']['password']
        }
    else:
        # 默认配置
        print(f"配置文件不存在: {config_path}")
        print("使用默认Neo4j配置")
        return {
            'uri': 'bolt://localhost:7687',
            'user': 'neo4j',
            'password': 'password'
        }


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='知识图谱反向追踪脚本')
    parser.add_argument('--direction', type=str, required=True, choices=['both'], help='追踪方向')
    parser.add_argument('--code', type=str, required=True, help='代码目录')
    
    args = parser.parse_args()
    
    # 加载Neo4j配置
    neo4j_config = load_neo4j_config()
    
    if not neo4j_config:
        return
    
    # 创建扫描器和追踪器
    scanner = CodeScanner()
    tracer = Neo4jTracer(
        uri=neo4j_config['uri'],
        user=neo4j_config['user'],
        password=neo4j_config['password']
    )
    
    try:
        # 扫描代码目录
        print(f"扫描代码目录: {args.code}")
        code_map = scanner.scan_directory(args.code)
        
        if not code_map:
            print("未找到任何类")
            return
        
        # 导入代码文件
        tracer.import_code_files(code_map)
        
        # 导入实现关系
        tracer.import_implement_relations(code_map)
        
        # 导入代码追踪关系
        tracer.import_code_traces(code_map)
        
        # 验证连接
        tracer.verify_connections()
        
        print("\n反向追踪完成!")
        
    finally:
        tracer.close()


if __name__ == "__main__":
    main()
