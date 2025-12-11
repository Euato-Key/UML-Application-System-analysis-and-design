from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    应用配置类
    """
    # 图数据库配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # MQTT配置
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = "mqtt"
    MQTT_PASSWORD: Optional[str] = "password"
    
    # LLM配置
    LLM_API_KEY: str = "test-api-key"
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # 应用配置
    APP_NAME: str = "物联网设备知识图谱交互管理平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"  # 支持从.env文件加载配置
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
