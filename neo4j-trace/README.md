# 知识图谱追踪脚本

用于构建和管理物联网设备知识图谱的追踪脚本，实现需求-设计-代码的双向追踪，支持多种UC编号格式的统一处理。

## 脚本功能

### 1. kg_build.py
设计阶段知识图谱构建脚本，用于解析PlantUML文件并导入Neo4j数据库。

**功能：**
- 解析用例图（系统级用例图、业务用例图），提取用例节点
- 解析类图、包图和序列图，提取类、接口、组件和操作节点
- 建立类与用例之间的追踪关系
- 建立类之间的依赖关系和继承关系
- 支持UC编号格式的统一处理（UC-XX → UCXX）
- 支持多文件批量解析和构建

### 2. kg_trace.py
代码阶段知识图谱追踪脚本，用于扫描代码文件并建立代码与类之间的关系。

**功能：**
- 扫描Python代码文件（支持目录递归扫描）
- 提取类定义和Docstring中的追踪标记（Trace: [xxx]格式）
- 建立代码文件与类之间的实现关系
- 支持UC编号格式的统一处理（UC-XX → UCXX）
- 验证需求-类-代码的三级关系
- 支持正向追踪（需求→类→代码）和反向追踪（代码→类→需求）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

脚本会自动加载 `服务器的neo4j配置.json` 中的Neo4j连接配置。如果配置文件不存在，将使用默认配置：

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
# 解析需求阶段文件（用例图、活动图）
python kg_build.py --stage requirement --files ../src/2_req/03-系统级用例图.puml ../src/2_req/02-2-UC-02-构建拓扑关系-活动图.puml

# 解析设计阶段文件（类图、包图、序列图）
python kg_build.py --stage design --files ../src/3_design/01-包图.puml ../src/3_design/类图.puml ../src/3_design/UC-02-维护图谱拓扑序列图.puml

# 批量解析多个文件
python kg_build.py --stage requirement --files ../src/2_req/*.puml ../src/3_design/*.puml

# 清空数据库并重新构建
python kg_build.py --stage requirement --files ../src/2_req/*.puml --clear
```

### 2. 建立代码追踪关系

```bash
# 扫描代码目录，建立双向追踪
python kg_trace.py --direction both --code "../src/4_code/iot-kg-platform/app"

# 仅正向追踪（从用例到代码）
python kg_trace.py --direction forward --code "../src/4_code/iot-kg-platform/app"

# 仅反向追踪（从代码到用例）
python kg_trace.py --direction backward --code "../src/4_code/iot-kg-platform/app"
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
MATCH (uc:UseCase {id: 'UC02'})<-[:TRACE]-(c:Class)<-[:IMPLEMENTS]-(f:CodeFile)
RETURN uc.id, c.name, f.path
```

### 5. 查询所有三级追踪关系示例
```cypher
MATCH (uc:UseCase)<-[:TRACE]-(c:Class)<-[:IMPLEMENTS]-(f:CodeFile)
RETURN uc.id, uc.name, c.name, f.path
```

## 项目结构

```
neo4j-trace/
├── kg_build.py                 # 设计阶段知识图谱构建脚本
├── kg_trace.py                 # 代码阶段追踪脚本
├── requirements.txt            # 依赖列表
├── README.md                   # 使用说明
├── 服务器的neo4j配置.json        # Neo4j服务器配置
└── .venv/                      # Python虚拟环境（可选）
```

## 版本更新说明

### v1.1 更新内容
- 支持UC编号格式的统一处理（自动将UC-XX格式转换为UCXX格式）
- 改进了用例图和类图的解析逻辑
- 增加了活动图和序列图的解析支持
- 优化了Neo4j连接配置的加载方式
- 修复了路径处理和文件查找的问题

## 常见问题

### 1. UC编号格式问题
脚本会自动处理不同格式的UC编号，如UC-02、UC02、UC-4等，统一转换为UCXX格式（如UC02、UC04）。

### 2. 文件路径问题
请确保提供的文件路径正确，脚本支持相对路径和绝对路径。

### 3. Neo4j连接问题
请检查`服务器的neo4j配置.json`文件中的连接信息是否正确，确保Neo4j服务正在运行。
