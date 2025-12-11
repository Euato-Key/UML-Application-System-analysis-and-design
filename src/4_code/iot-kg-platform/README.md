# 物联网设备知识图谱交互管理平台

基于Neo4j和FastAPI的物联网设备知识图谱管理系统，用于实现设备拓扑管理、智能问答和设备生命周期管理。

## 项目结构

```
iot-kg-platform/
├── app/
│   ├── __init__.py              # 应用包初始化
│   ├── main.py                  # 应用入口文件
│   ├── config.py                # 配置文件
│   ├── domain/                  # 领域实体层
│   │   ├── __init__.py
│   │   └── models.py            # 领域模型定义
│   ├── infra/                   # 基础设施层
│   │   ├── __init__.py
│   │   ├── graph_db.py          # Neo4j 连接与仓储
│   │   ├── llm_client.py        # 大模型接口
│   │   └── mqtt_client.py       # IoT 连接器
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── topology_svc.py      # 拓扑管理服务 (UC-02)
│   │   ├── agent_svc.py         # 智能问答服务 (UC-04)
│   │   └── lifecycle_svc.py     # 设备生命周期服务 (UC-01, 07)
│   └── api/                     # 接口层
│       ├── __init__.py
│       └── routers.py           # FastAPI 路由
├── trace_tool.py                # 需求追踪工具
├── requirements.txt             # 依赖声明
└── README.md                    # 项目说明
```

## 功能模块

### 1. 领域模型 (Domain Layer)
- `Device`: 设备基类
- `Space`: 物理空间
- `Gateway`: 网关设备
- `Sensor`: 传感器设备
- `Firmware`: 固件信息

### 2. 基础设施层 (Infrastructure Layer)
- `GraphRepository`: Neo4j 图数据库接口
- `LLMClient`: 大模型客户端接口
- `IoTConnector`: IoT 设备连接器接口

### 3. 业务逻辑层 (Service Layer)
- `TopologyService`: 拓扑管理服务 (UC-02)
- `AgentService`: 智能问答服务 (UC-04)
- `LifecycleService`: 设备生命周期服务 (UC-01, 06, 07)

### 4. API 接口层
- 拓扑管理接口
- 智能问答接口
- 设备生命周期管理接口

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件，配置数据库和MQTT等参数：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=mqtt
MQTT_PASSWORD=your_password
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 需求追踪

使用 `trace_tool.py` 工具可以生成需求追踪报告：

```bash
python trace_tool.py
```

## 技术栈

- **Web框架**: FastAPI
- **数据库**: Neo4j
- **MQTT客户端**: paho-mqtt
- **配置管理**: pydantic-settings
- **API文档**: Swagger/OpenAPI

## 许可证

MIT License
