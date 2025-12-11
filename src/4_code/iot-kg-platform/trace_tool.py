#!/usr/bin/env python3
"""
需求追踪工具
用于分析代码中的Docstring，提取需求追踪标记，并生成追踪报告
"""

import os
import re
import argparse
from typing import Dict, List, Tuple


class TraceAnalyzer:
    """
    需求追踪分析器
    """
    
    def __init__(self, root_dir: str):
        """
        初始化分析器
        
        Args:
            root_dir: 项目根目录
        """
        self.root_dir = root_dir
        self.trace_pattern = r'Trace:\s*\[(UC-\d+)\]'
        self.trace_map: Dict[str, List[Tuple[str, str]]] = {}
        
    def analyze_file(self, file_path: str) -> None:
        """
        分析单个文件，提取需求追踪标记
        
        Args:
            file_path: 文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取Docstring中的追踪标记
            docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
            
            for docstring in docstrings:
                matches = re.findall(self.trace_pattern, docstring)
                if matches:
                    # 获取当前函数/类名
                    code_after = content.split(docstring)[1]
                    
                    # 尝试匹配类定义
                    class_match = re.match(r'\s*class\s+(\w+)', code_after)
                    if class_match:
                        entity_name = f"Class: {class_match.group(1)}"
                    else:
                        # 尝试匹配函数定义
                        func_match = re.match(r'\s*def\s+(\w+)', code_after)
                        if func_match:
                            entity_name = f"Function: {func_match.group(1)}"
                        else:
                            entity_name = "Unknown"
                    
                    # 记录追踪信息
                    relative_path = os.path.relpath(file_path, self.root_dir)
                    for uc in matches:
                        if uc not in self.trace_map:
                            self.trace_map[uc] = []
                        self.trace_map[uc].append((relative_path, entity_name))
        
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
    
    def analyze_directory(self, dir_path: str) -> None:
        """
        递归分析目录下的所有Python文件
        
        Args:
            dir_path: 目录路径
        """
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
    
    def generate_report(self) -> None:
        """
        生成需求追踪报告
        """
        print("=" * 60)
        print("物联网设备知识图谱交互管理平台 - 需求追踪报告")
        print("=" * 60)
        
        if not self.trace_map:
            print("未找到任何需求追踪标记")
            return
        
        # 按UC编号排序
        sorted_ucs = sorted(self.trace_map.keys())
        
        for uc in sorted_ucs:
            print(f"\n[UC] {uc}")
            print("-" * 30)
            
            # 按文件路径分组
            file_groups = {}
            for file_path, entity_name in self.trace_map[uc]:
                if file_path not in file_groups:
                    file_groups[file_path] = []
                file_groups[file_path].append(entity_name)
            
            # 打印每个文件中的实体
            for file_path, entities in file_groups.items():
                print(f"文件: {file_path}")
                for entity in entities:
                    print(f"  - {entity}")
        
        print(f"\n=" * 60)
        print(f"共追踪到 {len(self.trace_map)} 个需求，分布在 {sum(len(v) for v in self.trace_map.values())} 个实体中")
        print("=" * 60)


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='需求追踪工具')
    parser.add_argument('--root', '-r', default='.', help='项目根目录')
    args = parser.parse_args()
    
    analyzer = TraceAnalyzer(args.root)
    analyzer.analyze_directory(args.root)
    analyzer.generate_report()


if __name__ == "__main__":
    main()
