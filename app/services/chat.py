import io
import requests
import logging
from PIL import Image
from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any

# 导入模型
from app.models import ChatMessage, ChatResponse

# 导入配置
from app.config import SILICON_FLOW_API_KEY, SILICON_FLOW_API_URL, SILICON_FLOW_MODEL

# 导入工具函数
from app.utils.image import encode_image_to_base64

# 配置日志
logger = logging.getLogger(__name__)

async def perform_chat(file: UploadFile, prompt: str = "请描述这张图片", history: Optional[List[Dict[str, str]]] = None):
    """
    与模型进行多轮对话，支持图像理解
    
    - **file**: 图片文件
    - **prompt**: 用户提问
    - **history**: 可选的对话历史
    """
    if not SILICON_FLOW_API_KEY:
        raise HTTPException(status_code=500, detail="未配置API密钥，请在app/config.py文件中设置SILICON_FLOW_API_KEY")
    
    try:
        # 读取上传的图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 将图片转换为base64编码
        base64_image = encode_image_to_base64(image)
        
        # 准备消息历史
        messages = []
        
        # 添加历史消息
        if history:
            for item in history:
                if "user" in item and item["user"]:
                    messages.append({"role": "user", "content": [{"type": "text", "text": item["user"]}]})
                if "assistant" in item and item["assistant"]:
                    messages.append({"role": "assistant", "content": [{"type": "text", "text": item["assistant"]}]})
        
        # 添加当前用户消息（包含图片）
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]
        })
        
        # 准备请求数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
        }
        
        # 在 payload 中使用配置的模型名称
        payload = {
            "model": SILICON_FLOW_MODEL,
            "messages": messages,
            "max_tokens": 2048
        }
        
        # 发送请求到Silicon Flow API
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"API请求失败: {response.text}")
        
        # 解析响应
        result = response.json()
        assistant_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 更新历史
        if not history:
            history = []
        
        # 添加当前对话到历史
        history.append({"user": prompt, "assistant": assistant_response})
        
        # 返回结果
        return JSONResponse(content={
            "response": assistant_response,
            "history": history,
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"聊天处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")