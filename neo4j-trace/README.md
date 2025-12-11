# 知识图谱追踪脚本

用于构建和管理物联网设备知识图谱的追踪脚本，实现需求-设计-代码的双向追踪。

## 脚本功能

### 1. kg_build.py
设计阶段知识图谱构建脚本，用于解析PlantUML文件并导入Neo4j数据库。

**功能：**
- 解析用例图，提取用例节点
- 解析类图，提取类和操作节点
- 建立类与用例之间的追踪关系
- 建立类之间的依赖关系

### 2. kg_trace.py
代码阶段知识图谱追踪脚本，用于扫描代码文件并建立代码与类之间的关系。

**功能：**
- 扫描Python代码文件
- 提取类定义和Docstring中的追踪标记
- 建立代码文件与类之间的实现关系
- 验证需求-类-代码的三级关系

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

脚本会自动加载 `../../../服务器的neo4j配置.json` 中的Neo4j连接配置。如果配置文件不存在，将使用默认配置：

```json
{
  "uri": "bolt://localhost:7687",
  "user": "neo4j",
  "password": "password"
}
```

## 使用方法

### 1. 构建设计阶段知识图谱

```bash
# 解析类图文件
python kg_build.py --stage design --files ../../../3_design/01-包图.puml ../../../3_design/03-类图.md

# 解析用例图文件
python kg_build.py --stage design --files ../../../2_req/03-系统级用例图.puml

# 清空数据库并重新构建
python kg_build.py --stage design --files *.puml --clear
```

### 2. 建立代码追踪关系

```bash
# 扫描代码目录，建立双向追踪
python kg_trace.py --direction both --code ../iot-kg-platform
```

## Neo4j查询示例

### 1. 查询所有用例
```cypher
MATCH (uc:UseCase) RETURN uc.id, uc.name
```

### 2. 查询所有类
```cypher
MATCH (c:Class) RETURN c.name
```

### 3. 查询需求-类-代码三级关系
```cypher
MATCH (uc:UseCase)<-[:TRACE]-(c:Class)<-[:IMPLEMENTS]-(f:CodeFile)
RETURN uc.id, c.name, f.path
```

### 4. 查询特定用例相关的类和代码
```cypher
MATCH (uc:UseCase {id: 'UC-02'})<-[:TRACE]-(c:Class)<-[:IMPLEMENTS]-(f:CodeFile)
RETURN uc.id, c.name, f.path
```

## 项目结构

```
neo4j-trace/
├── kg_build.py       # 设计阶段知识图谱构建脚本
├── kg_trace.py       # 代码阶段追踪脚本
├── requirements.txt  # 依赖列表
└── README.md         # 使用说明
```
