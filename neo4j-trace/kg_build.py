#!/usr/bin/env python3
"""
知识图谱构建脚本
用于解析PlantUML文件，提取实体和关系，并导入到Neo4j数据库中
"""

import os
import re
from neo4j import GraphDatabase
import argparse
import json

class PlantUMLParser:
    def __init__(self):
        self.use_cases = []
        self.classes = []
        self.dependencies = []
        self.components = []
        self.activities = []  # 新增：存储活动图信息
    
    def parse(self, file_path):
        """解析PlantUML文件，提取用例、类和依赖关系"""
        print(f"正在解析文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果是Markdown文件，提取PlantUML代码块
        if file_path.endswith('.md'):
            plantuml_blocks = re.findall(r'```plantuml\s*(.*?)\s*```', content, re.DOTALL)
            if plantuml_blocks:
                content = '\n'.join(plantuml_blocks)
        
        # 根据文件名判断图的类型
        if '活动图' in file_path or '序列图' in file_path or '流程图' in file_path:
            self._parse_activity_diagram(content, file_path)
        elif '类图' in file_path:
            # 解析类
            self._parse_classes(content)
            
            # 解析依赖关系
            self._parse_dependencies(content)
            
            # 解析组件
            self._parse_components(content)
        elif '用例图' in file_path:
            self._parse_use_case_diagram(content)
        else:
            # 尝试解析所有类型
            self._parse_classes(content)
            self._parse_dependencies(content)
            self._parse_components(content)
            self._parse_activity_diagram(content, file_path)
        
        print(f"解析完成: {file_path}")
        print(f"  找到 {len(self.classes)} 个类")
        print(f"  找到 {len(self.dependencies)} 个依赖关系")
        print(f"  找到 {len(self.components)} 个组件")
        print(f"  找到 {len(self.activities)} 个活动")
        print(f"  找到 {len(self.use_cases)} 个用例")
    
    def _parse_classes(self, content):
        """解析类定义"""
        # 提取所有类定义（支持不同格式）
        class_patterns = [
            r'class\s+"?([^"]+)"?\s+as\s+([^\s]+)\s*\{([^\}]+)\}',  # 带别名和内容
            r'class\s+"?([^"]+)"?\s+as\s+([^\s]+)',  # 只带别名
            r'class\s+"?([^"]+)"?\s*\{([^\}]+)\}',  # 有内容无别名
            r'class\s+"?([^"]+)"?\s*'  # 简单类定义
        ]
        
        for pattern in class_patterns:
            classes = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for class_def in classes:
                if len(class_def) == 3:
                    # 带别名和内容
                    class_name, class_id, class_content = class_def
                elif len(class_def) == 2:
                    # 只有类名和内容
                    class_name, class_content = class_def
                    class_id = class_name.replace(' ', '_').replace('"', '')
                elif len(class_def) == 1:
                    # 只有类名
                    class_name = class_def[0]
                    class_id = class_name.replace(' ', '_').replace('"', '')
                    class_content = ''
                else:
                    continue
                
                # 解析类的属性
                attr_pattern = r'\s*[-+#]\s+([^:]+)\s*:\s*([^\n]+)'
                attributes = re.findall(attr_pattern, class_content)
                
                # 解析需求追踪
                trace_pattern = r'\[UC-\d+[\s,]*UC-\d+[^\]]*\]'
                traces = re.findall(trace_pattern, class_content)
                
                # 检查是否已存在该类
                existing = next((c for c in self.classes if c['id'] == class_id), None)
                if not existing:
                    self.classes.append({
                        'name': class_name,
                        'id': class_id,
                        'attributes': [{'name': attr[0].strip(), 'type': attr[1].strip()} for attr in attributes],
                        'traces': traces
                    })
    
    def _parse_use_case_diagram(self, content):
        """解析用例图"""
        # 提取用例
        use_case_patterns = [
            r'usecase\s+"?([^"]+)"?\s+as\s+([^\s]+)',
            r'usecase\s+"?([^"]+)"?'
        ]
        
        for pattern in use_case_patterns:
            use_cases = re.findall(pattern, content)
            for uc in use_cases:
                if len(uc) == 2:
                    use_case_name, use_case_id = uc
                else:
                    use_case_name = uc[0]
                    use_case_id = use_case_name.replace(' ', '_').replace('"', '')
                
                # 检查是否已存在
                existing = next((u for u in self.use_cases if u['id'] == use_case_id), None)
                if not existing:
                    self.use_cases.append({
                        'name': use_case_name,
                        'id': use_case_id
                    })
    
    def _parse_activity_diagram(self, content, file_path):
        """解析活动图"""
        # 从文件名中提取UC编号（支持UC-01或UC01格式）
        uc_match = re.search(r'UC[-]?(\d+)', file_path)
        if uc_match:
            uc_id = f'UC{uc_match.group(1)}'
        else:
            uc_id = 'UNKNOWN'
        
        # 提取活动节点
        activity_patterns = [
            r':([^:]+);',  # 基本活动节点
            r'start\s*',  # 开始节点
            r'end\s*'  # 结束节点
        ]
        
        activities = []
        for pattern in activity_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.strip():
                    activities.append(match.strip())
        
        # 提取箭头关系
        arrow_pattern = r'->\s*"?([^"]*)"?'
        arrows = re.findall(arrow_pattern, content)
        
        self.activities.append({
            'uc_id': uc_id,
            'file_path': file_path,
            'activities': activities,
            'arrows': arrows
        })
    
    def _parse_dependencies(self, content):
        """解析依赖关系"""
        # 提取所有关系（支持更多类型和方向）
        relation_pattern = r'(\w+)\s*(<\|--|--|\.\.>|o--|\*--|--\*|--o|\\--|//--|-->|<--|\.\.\||o\.\.|\*\.\.|<\*\-\-|\-\-\*>|\<\|\.\.|\.\.\|>)\s*(\w+)'
        relations = re.findall(relation_pattern, content)
        
        for relation in relations:
            source, relation_type, target = relation
            self.dependencies.append({
                'source': source,
                'type': relation_type,
                'target': target
            })
    
    def _parse_components(self, content):
        """解析组件"""
        # 提取所有包定义
        package_pattern = r'package\s+"?([^"]+)"?\s*\{([^\}]+)\}'
        packages = re.findall(package_pattern, content, re.MULTILINE | re.DOTALL)
        
        for package in packages:
            package_name, package_content = package
            
            # 提取包内的类
            class_pattern = r'class\s+"?([^"]+)"?\s+as\s+([^\s]+)'
            classes = re.findall(class_pattern, package_content)
            
            self.components.append({
                'name': package_name,
                'classes': [cls[1] for cls in classes]  # 存储类ID
            })

class Neo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"已连接到Neo4j: {uri}")
    
    def close(self):
        self.driver.close()
        print("已关闭Neo4j连接")
    
    def import_use_cases(self, use_cases):
        """导入用例到Neo4j"""
        with self.driver.session() as session:
            for uc in use_cases:
                print(f"导入用例: {uc['name']} ({uc['id']})")
                session.run("""
                    MERGE (uc:UseCase {id: $id, name: $name})
                """, id=uc['id'], name=uc['name'])
    
    def import_classes(self, classes):
        """导入类和属性到Neo4j"""
        with self.driver.session() as session:
            for cls in classes:
                print(f"导入类: {cls['name']} ({cls['id']})")
                # 创建类节点
                session.run("""
                    MERGE (c:Class {id: $id, name: $name})
                """, id=cls['id'], name=cls['name'])
                
                # 创建属性节点并建立关系
                for attr in cls['attributes']:
                    session.run("""
                        MATCH (c:Class {id: $class_id})
                        MERGE (a:Attribute {name: $name, type: $type})
                        MERGE (c)-[:HAS_ATTRIBUTE]->(a)
                    """, name=attr['name'], type=attr['type'], class_id=cls['id'])
                
                # 处理需求追踪
                for trace in cls['traces']:
                    # 提取UC编号（支持多个，格式：UC01 或 UC-01）
                    uc_matches = re.findall(r'UC[-]?(\d+)', trace)
                    for uc_number in uc_matches:
                        uc_id = f'UC{uc_number}'
                        session.run("""
                            MATCH (c:Class {id: $class_id})
                            MERGE (uc:UseCase {id: $uc_id})
                            MERGE (c)-[:SUPPORTS]->(uc)
                        """, uc_id=uc_id, class_id=cls['id'])
    
    def import_activities(self, activities):
        """导入活动图信息到Neo4j"""
        with self.driver.session() as session:
            for activity_info in activities:
                uc_id = activity_info['uc_id']
                
                # 确保用例节点存在
                session.run("""
                    MERGE (uc:UseCase {id: $uc_id})
                """, uc_id=uc_id)
                
                for activity in activity_info['activities']:
                    # 创建活动节点
                    activity_id = activity.replace(' ', '_').replace('"', '')[:50]  # 限制长度
                    session.run("""
                        MATCH (uc:UseCase {id: $uc_id})
                        MERGE (a:Activity {id: $id, name: $name})
                        MERGE (uc)-[:INCLUDES]->(a)
                    """, uc_id=uc_id, id=activity_id, name=activity)
                
                # 创建文件引用
                session.run("""
                    MATCH (uc:UseCase {id: $uc_id})
                    MERGE (f:UMLFile {path: $path, type: 'ActivityDiagram'})
                    MERGE (uc)-[:HAS_DIAGRAM]->(f)
                """, uc_id=uc_id, path=activity_info['file_path'])
    
    def import_dependencies(self, dependencies):
        """导入依赖关系到Neo4j"""
        with self.driver.session() as session:
            for dep in dependencies:
                relation_type = self._map_relation_type(dep['type'])
                
                print(f"导入关系: {dep['source']} {relation_type} {dep['target']}")
                session.run("""
                    MATCH (s:Class {id: $source}), (t:Class {id: $target})
                    MERGE (s)-[r:%s]->(t)
                """ % relation_type, source=dep['source'], target=dep['target'])
    
    def import_components(self, components):
        """导入组件和依赖关系到Neo4j"""
        with self.driver.session() as session:
            for comp in components:
                print(f"导入组件: {comp['name']}")
                # 创建组件节点
                session.run("""
                    MERGE (c:Component {name: $name})
                """, name=comp['name'])
                
                # 建立组件和类的关系
                for class_id in comp['classes']:
                    session.run("""
                        MATCH (comp:Component {name: $comp_name}), (cls:Class {id: $class_id})
                        MERGE (comp)-[:CONTAINS]->(cls)
                    """, comp_name=comp['name'], class_id=class_id)
    
    def _map_relation_type(self, plantuml_type):
        """将PlantUML关系类型映射到Neo4j关系类型"""
        relation_map = {
            '<|--': 'INHERITS_FROM',
            '--': 'ASSOCIATED_WITH',
            '..>': 'DEPENDS_ON',
            'o--': 'AGGREGATES',
            '*--': 'COMPOSES'
        }
        return relation_map.get(plantuml_type, 'RELATES_TO')

class KGBuilder:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.parser = PlantUMLParser()
        self.importer = Neo4jImporter(neo4j_uri, neo4j_user, neo4j_password)
    
    def build(self, stage, files):
        """构建知识图谱"""
        print(f"开始构建 {stage} 阶段知识图谱")
        
        for file_path in files:
            if os.path.exists(file_path):
                self.parser.parse(file_path)
            else:
                print(f"文件不存在: {file_path}")
        
        # 导入到Neo4j
        if stage == 'design':
            # 先导入用例，因为类和活动都依赖于用例
            self.importer.import_use_cases(self.parser.use_cases)
            # 导入类和依赖
            self.importer.import_classes(self.parser.classes)
            self.importer.import_dependencies(self.parser.dependencies)
            self.importer.import_components(self.parser.components)
            # 导入活动图信息
            self.importer.import_activities(self.parser.activities)
        elif stage == 'component':
            self.importer.import_components(self.parser.components)
        elif stage == 'requirement':
            self.importer.import_use_cases(self.parser.use_cases)
            self.importer.import_activities(self.parser.activities)
        
        self.importer.close()
        print(f"{stage} 阶段知识图谱构建完成")

def main():
    parser = argparse.ArgumentParser(description='构建知识图谱')
    parser.add_argument('--stage', choices=['design', 'component', 'requirement'], required=True, help='构建阶段')
    parser.add_argument('--files', nargs='+', required=True, help='PlantUML文件路径')
    parser.add_argument('--config', default='服务器的neo4j配置.json', help='Neo4j配置文件路径')
    
    args = parser.parse_args()
    
    # 从配置文件读取Neo4j连接信息
    config_path = args.config
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 解析配置文件结构
        neo4j_uri = config['endpoints']['bolt']
        neo4j_user = config['credentials']['username']
        neo4j_password = config['credentials']['password']
        
        kg_builder = KGBuilder(
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password
        )
        
        kg_builder.build(args.stage, args.files)
    else:
        print(f"配置文件不存在: {config_path}")
        print("请创建包含Neo4j连接信息的配置文件")

if __name__ == '__main__':
    main()