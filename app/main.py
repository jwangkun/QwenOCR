from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 导入API路由
from app.api import router

# 导入配置
from app.config import SILICON_FLOW_API_KEY

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Qwen-2.5-VL OCR API",
    description="使用通义千问2.5视觉语言模型进行OCR识别的API",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    在应用启动时检查API密钥
    """
    if not SILICON_FLOW_API_KEY:
        logger.warning("未在配置文件中设置SILICON_FLOW_API_KEY，请确保在app/config.py中设置了正确的API密钥")

# 注册API路由
app.include_router(router, prefix="")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
