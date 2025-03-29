from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import logging

# 导入服务
from app.services.ocr import perform_ocr, perform_structured_ocr
from app.services.chat import perform_chat

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()

@router.get("/")
async def root():
    """
    API根路径，返回欢迎信息
    """
    return {"message": "欢迎使用Qwen-2.5-VL OCR API"}

@router.post("/ocr")
async def ocr(
    file: UploadFile = File(...),
    prompt: Optional[str] = "请识别图片中的所有文字内容，并按照原始布局输出",
    json_format: Optional[bool] = False
):
    """
    OCR接口，上传图片并返回识别结果
    
    - **file**: 要识别的图片文件
    - **prompt**: 可选的提示词，默认为识别所有文字
    - **json_format**: 是否将OCR结果转换为JSON格式，默认为True
    """
    return await perform_ocr(file, prompt, json_format)

@router.post("/structured_ocr")
async def structured_ocr(
    file: UploadFile = File(...),
    topics: Optional[List[str]] = None,
    languages: Optional[str] = "中文"
):
    """
    结构化OCR接口，上传图片并返回结构化的OCR结果
    
    - **file**: 要识别的图片文件
    - **topics**: 可选的主题列表，用于指导OCR识别的内容类型
    - **languages**: 可选的语言参数，默认为中文
    """
    return await perform_structured_ocr(file, topics, languages)

@router.post("/chat")
async def chat(
    file: UploadFile = File(...),
    prompt: str = "请描述这张图片",
    history: Optional[List[Dict[str, str]]] = None
):
    """
    与模型进行多轮对话，支持图像理解
    
    - **file**: 图片文件
    - **prompt**: 用户提问
    - **history**: 可选的对话历史
    """
    return await perform_chat(file, prompt, history)