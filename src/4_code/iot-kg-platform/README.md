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

## API接口文档

### 1. 基础接口

#### 根路径
```
GET /
```
返回API基本信息

**响应示例**：
```json
{
  "message": "物联网设备知识图谱交互管理平台API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### 健康检查
```
GET /health
```
检查服务健康状态

**响应示例**：
```json
{
  "status": "healthy",
  "service": "iot-kg-platform"
}
```

### 2. 拓扑管理接口

#### 绑定拓扑关系
```
POST /api/v1/topology/bind
```
绑定设备与空间、网关的拓扑关系

**请求体**：
```json
{
  "device_id": "sensor-001",
  "space_id": "room-001",
  "gateway_id": "gateway-001"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "拓扑绑定成功",
  "data": {
    "device_id": "sensor-001",
    "space_id": "room-001",
    "gateway_id": "gateway-001"
  }
}
```

#### 构建网络关联
```
POST /api/v1/topology/associate
```
构建传感器与网关的网络关联

**请求体**：
```json
{
  "sensor_id": "sensor-001",
  "gateway_id": "gateway-001"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "网络关联构建成功",
  "data": {
    "sensor_id": "sensor-001",
    "gateway_id": "gateway-001"
  }
}
```

#### 获取设备影响范围
```
GET /api/v1/topology/impact/{device_id}
```
获取设备故障时的影响范围

**响应示例**：
```json
{
  "devices": ["sensor-001", "sensor-002", "gateway-001"]
}
```

### 3. 智能问答接口

#### 智能问答
```
POST /api/v1/agent/ask
```
向智能体提问关于设备知识图谱的问题

**请求体**：
```json
{
  "question": "设备sensor-001连接到哪个网关？"
}
```

**响应示例**：
```json
{
  "success": true,
  "answer": "设备sensor-001连接到网关gateway-001",
  "confidence": 0.95
}
```

### 4. 设备生命周期接口

#### 注册设备
```
POST /api/v1/lifecycle/register
```
注册新设备到知识图谱

**请求体**：
```json
{
  "device_id": "sensor-001",
  "name": "温度传感器",
  "type": "Sensor",
  "status": "在线",
  "firmware_version": "1.0.0",
  "accuracy": 0.5,
  "unit": "℃"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "设备注册成功",
  "device_id": "sensor-001"
}
```

#### 灰度升级固件
```
POST /api/v1/lifecycle/upgrade
```
对设备进行固件灰度升级

**请求体**：
```json
{
  "version": "2.0.0",
  "device_ids": ["sensor-001", "sensor-002"]
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "固件升级成功",
  "upgraded_devices": ["sensor-001", "sensor-002"]
}
```

#### 退役设备
```
POST /api/v1/lifecycle/decommission/{device_id}
```
退役报废设备

**响应示例**：
```json
{
  "success": true,
  "message": "设备退役成功",
  "device_id": "sensor-001"
}
```

## 测试命令行示例

### 使用curl命令测试

#### 测试健康检查接口
```bash
curl -X GET http://localhost:8000/health
```

#### 测试设备注册接口
```bash
curl -X POST http://localhost:8000/api/v1/lifecycle/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"sensor-001","name":"温度传感器","type":"Sensor","status":"在线","firmware_version":"1.0.0","accuracy":0.5,"unit":"℃"}'
```

#### 测试拓扑绑定接口
```bash
curl -X POST http://localhost:8000/api/v1/topology/bind \
  -H "Content-Type: application/json" \
  -d '{"device_id":"sensor-001","space_id":"room-001","gateway_id":"gateway-001"}'
```

#### 测试智能问答接口
```bash
curl -X POST http://localhost:8000/api/v1/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"设备sensor-001连接到哪个网关？"}'
```

### 使用Python requests库测试

创建测试脚本 `test_api.py`：

```python
import requests

BASE_URL = "http://localhost:8000"

# 测试健康检查
def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    print("健康检查:", response.json())

# 测试设备注册
def test_register_device():
    data = {
        "device_id": "sensor-001",
        "name": "温度传感器",
        "type": "Sensor",
        "status": "在线",
        "firmware_version": "1.0.0",
        "accuracy": 0.5,
        "unit": "℃"
    }
    response = requests.post(f"{BASE_URL}/api/v1/lifecycle/register", json=data)
    print("设备注册:", response.json())

# 测试拓扑绑定
def test_bind_topology():
    data = {
        "device_id": "sensor-001",
        "space_id": "room-001",
        "gateway_id": "gateway-001"
    }
    response = requests.post(f"{BASE_URL}/api/v1/topology/bind", json=data)
    print("拓扑绑定:", response.json())

# 测试智能问答
def test_ask_question():
    data = {
        "question": "设备sensor-001连接到哪个网关？"
    }
    response = requests.post(f"{BASE_URL}/api/v1/agent/ask", json=data)
    print("智能问答:", response.json())

if __name__ == "__main__":
    test_health_check()
    test_register_device()
    test_bind_topology()
    test_ask_question()
```

运行测试脚本：
```bash
python test_api.py
```

## 技术栈

- **Web框架**: FastAPI
- **数据库**: Neo4j
- **MQTT客户端**: paho-mqtt
- **配置管理**: pydantic-settings
- **API文档**: Swagger/OpenAPI

## 许可证

MIT License
