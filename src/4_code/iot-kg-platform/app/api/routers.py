from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.services.topology_svc import TopologyService
from app.services.agent_svc import AgentService
from app.services.lifecycle_svc import LifecycleService
from app.infra.graph_db import GraphRepository
from app.infra.llm_client import LLMClient
from app.infra.mqtt_client import IoTConnector
from app.config import settings


# 创建路由实例
router = APIRouter()


# 配置依赖注入

def get_graph_repo() -> GraphRepository:
    """
    获取图数据库仓库实例
    """
    return GraphRepository(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )


def get_llm_client() -> LLMClient:
    """
    获取大模型客户端实例
    """
    return LLMClient(api_key=settings.LLM_API_KEY)


def get_iot_connector() -> IoTConnector:
    """
    获取IoT连接器实例
    """
    return IoTConnector(
        broker=settings.MQTT_BROKER,
        port=settings.MQTT_PORT,
        username=settings.MQTT_USERNAME or "",
        password=settings.MQTT_PASSWORD or ""
    )


def get_topology_service(graph_repo: GraphRepository = Depends(get_graph_repo)) -> TopologyService:
    """
    获取拓扑服务实例
    """
    return TopologyService(graph_repo)


def get_agent_service(
    graph_repo: GraphRepository = Depends(get_graph_repo),
    llm_client: LLMClient = Depends(get_llm_client)
) -> AgentService:
    """
    获取智能体服务实例
    """
    return AgentService(graph_repo, llm_client)


def get_lifecycle_service(
    iot_connector: IoTConnector = Depends(get_iot_connector),
    graph_repo: GraphRepository = Depends(get_graph_repo)
) -> LifecycleService:
    """
    获取生命周期服务实例
    """
    return LifecycleService(iot_connector, graph_repo)


# 请求模型

class TopologyBindRequest(BaseModel):
    """
    拓扑绑定请求模型
    """
    device_id: str
    space_id: str
    gateway_id: Optional[str] = None


class NetworkAssociationRequest(BaseModel):
    """
    网络关联请求模型
    """
    sensor_id: str
    gateway_id: str


class QuestionRequest(BaseModel):
    """
    智能问答请求模型
    """
    question: str


class DeviceRegistrationRequest(BaseModel):
    """
    设备注册请求模型
    """
    device_id: str
    name: str
    type: str = "Device"
    status: str = "离线"
    firmware_version: Optional[str] = None
    # 传感器特有字段
    accuracy: Optional[float] = None
    unit: Optional[str] = None
    # 网关特有字段
    max_connections: Optional[int] = None
    protocol_type: Optional[str] = None


class FirmwareUpgradeRequest(BaseModel):
    """
    固件升级请求模型
    """
    version: str
    device_ids: List[str]


# 拓扑服务路由 (UC-02)

@router.post("/topology/bind", tags=["拓扑管理"])
async def bind_topology(
    request: TopologyBindRequest,
    topology_svc: TopologyService = Depends(get_topology_service)
):
    """
    绑定拓扑关系
    Trace: [UC-02]
    """
    result = topology_svc.bind_topology(
        request.device_id,
        request.space_id,
        request.gateway_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.post("/topology/associate", tags=["拓扑管理"])
async def associate_network(
    request: NetworkAssociationRequest,
    topology_svc: TopologyService = Depends(get_topology_service)
):
    """
    构建网络关联
    Trace: [UC-02]
    """
    result = topology_svc.build_network_association(
        request.sensor_id,
        request.gateway_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/topology/impact/{device_id}", tags=["拓扑管理"])
async def get_impact_range(
    device_id: str,
    topology_svc: TopologyService = Depends(get_topology_service)
):
    """
    获取设备影响范围
    Trace: [UC-02]
    """
    result = topology_svc.get_impact_range(device_id)
    return {"devices": result}


# 智能体服务路由 (UC-04)

@router.post("/agent/ask", tags=["智能问答"])
async def ask_question(
    request: QuestionRequest,
    agent_svc: AgentService = Depends(get_agent_service)
):
    """
    智能问答
    Trace: [UC-04]
    """
    result = agent_svc.ask(request.question)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# 生命周期服务路由 (UC-01, UC-06, UC-07)

@router.post("/lifecycle/register", tags=["设备生命周期"])
async def register_device(
    request: DeviceRegistrationRequest,
    lifecycle_svc: LifecycleService = Depends(get_lifecycle_service)
):
    """
    注册设备
    Trace: [UC-01]
    """
    result = lifecycle_svc.register_device(request.model_dump())
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/lifecycle/upgrade", tags=["设备生命周期"])
async def upgrade_firmware(
    request: FirmwareUpgradeRequest,
    lifecycle_svc: LifecycleService = Depends(get_lifecycle_service)
):
    """
    灰度升级固件
    Trace: [UC-06]
    """
    result = lifecycle_svc.gray_upgrade_firmware(
        request.version,
        request.device_ids
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/lifecycle/decommission/{device_id}", tags=["设备生命周期"])
async def decommission_device(
    device_id: str,
    lifecycle_svc: LifecycleService = Depends(get_lifecycle_service)
):
    """
    退役设备
    Trace: [UC-07]
    """
    result = lifecycle_svc.decommission_device(device_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result
