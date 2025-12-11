from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class DeviceStatus(str, Enum):
    """
    设备状态枚举
    Trace: [UC-01, UC-03, UC-07]
    """
    ONLINE = "在线"
    OFFLINE = "离线"
    ALERT = "告警"
    RETIRED = "退役"


class SpaceType(str, Enum):
    """
    空间类型枚举
    Trace: [UC-02, UC-04]
    """
    BUILDING = "楼宇"
    FLOOR = "楼层"
    ROOM = "房间"


class AlertLevel(str, Enum):
    """
    告警级别枚举
    Trace: [UC-08]
    """
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class Device(BaseModel):
    """
    设备基类
    Trace: [UC-01, UC-03, UC-07]
    """
    device_id: str = Field(..., description="设备ID")
    name: str = Field(..., description="设备名称")
    status: DeviceStatus = Field(default=DeviceStatus.OFFLINE, description="在线状态")
    firmware_version: Optional[str] = Field(None, description="固件版本")
    certificate_id: Optional[str] = Field(None, description="证书ID")


class Gateway(Device):
    """
    网关设备
    Trace: [UC-01, UC-03, UC-07]
    """
    max_connections: int = Field(..., description="最大挂载数")
    protocol_type: str = Field(..., description="协议类型")


class Sensor(Device):
    """
    传感器设备
    Trace: [UC-01, UC-03, UC-07]
    """
    accuracy: float = Field(..., description="采集精度")
    unit: str = Field(..., description="数据单位")


class Space(BaseModel):
    """
    空间
    Trace: [UC-02, UC-04]
    """
    space_id: str = Field(..., description="空间ID")
    name: str = Field(..., description="空间名称")
    space_type: SpaceType = Field(..., description="空间类型")
    parent_id: Optional[str] = Field(None, description="父空间ID")


class FirmwarePackage(BaseModel):
    """
    固件包
    Trace: [UC-06]
    """
    version: str = Field(..., description="版本号")
    download_url: str = Field(..., description="下载地址")
    md5: str = Field(..., description="MD5校验码")
    release_time: str = Field(..., description="发布时间")


class SecurityAlert(BaseModel):
    """
    安全告警
    Trace: [UC-08]
    """
    alert_id: str = Field(..., description="告警ID")
    level: AlertLevel = Field(..., description="告警级别")
    timestamp: str = Field(..., description="发生时间")
    raw_message: str = Field(..., description="原始报文")
    device_id: str = Field(..., description="关联设备ID")
