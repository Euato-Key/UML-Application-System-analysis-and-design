from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router

# 创建FastAPI应用实例
app = FastAPI(
    title="物联网设备知识图谱交互管理平台",
    description="基于Neo4j和FastAPI的物联网设备知识图谱管理系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api/v1")


# 根路径
@app.get("/")
async def root():
    """
    API根路径
    """
    return {
        "message": "物联网设备知识图谱交互管理平台API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "iot-kg-platform"
    }
