import io
import requests
import logging
from PIL import Image
from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse
import json
import os
from typing import Optional, List, Dict, Any

# 导入模型
from app.models import OCRResponse, StructuredOCR

# 导入配置
from app.config import SILICON_FLOW_API_KEY, SILICON_FLOW_API_URL, SILICON_FLOW_MODEL

# 导入工具函数
from app.utils.image import encode_image_to_base64

# 配置日志
logger = logging.getLogger(__name__)

async def perform_ocr(file: UploadFile, prompt: Optional[str] = "请识别图片中的所有文字内容，并按照原始布局输出", json_format: Optional[bool] = False):
    """
    OCR接口，上传图片并返回识别结果
    
    - **file**: 要识别的图片文件
    - **prompt**: 可选的提示词，默认为识别所有文字
    - **json_format**: 是否将OCR结果转换为JSON格式，默认为True
    """
    if not SILICON_FLOW_API_KEY:
        raise HTTPException(status_code=500, detail="未配置API密钥，请在app/config.py文件中设置SILICON_FLOW_API_KEY")
    
    try:
        # 读取上传的图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 将图片转换为base64编码
        base64_image = encode_image_to_base64(image)
        
        # 准备请求数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
        }
        
        payload = {
            "model": SILICON_FLOW_MODEL,  # 使用配置文件中定义的模型名称
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 2048
        }
        
        # 发送请求到Silicon Flow API
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"API请求失败: {response.text}")
        
        # 解析响应
        result = response.json()
        text_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 直接返回原始文本结果，不进行任何格式转换或翻译
        return JSONResponse(content={
            "text": text_content,
            "status": "success"
        })
    
    except Exception as e:
        logger.error(f"OCR处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

async def perform_structured_ocr(file: UploadFile, topics: Optional[List[str]] = None, languages: Optional[str] = "中文"):
    """
    结构化OCR接口，上传图片并返回结构化的OCR结果
    
    - **file**: 要识别的图片文件
    - **topics**: 可选的主题列表，用于指导OCR识别的内容类型
    - **languages**: 可选的语言参数，默认为中文
    """
    if not SILICON_FLOW_API_KEY:
        raise HTTPException(status_code=500, detail="未配置API密钥，请在app/config.py文件中设置SILICON_FLOW_API_KEY")
    
    try:
        # 读取上传的图片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 将图片转换为base64编码
        base64_image = encode_image_to_base64(image)
        
        # 准备请求数据
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
        }
        
        # 构建OCR提示词
        ocr_prompt = "请识别图片中的所有文字内容，并按照原始布局输出"
        
        payload = {
            "model": SILICON_FLOW_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ocr_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                    ]
                }
            ],
            "max_tokens": 2048
        }
        
        # 发送请求到Silicon Flow API进行OCR识别
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"API请求失败: {response.status_code} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"API请求失败: {response.text}")
        
        # 解析响应
        result = response.json()
        text_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 准备结构化解析提示词
        topics_str = ", ".join(topics) if topics else "所有内容"
        structured_prompt = f"""这是图片的OCR识别结果：

{text_content}

请将上述OCR结果转换为结构化的JSON格式，包含以下内容：
1. 识别出的所有文本内容，按照合理的字典结构组织
2. 主题分类：{topics_str}
3. 语言：{languages}

只返回JSON对象，不要添加任何额外解释。"""
        
        structured_payload = {
            "model": SILICON_FLOW_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": structured_prompt}
                    ]
                }
            ],
            "max_tokens": 4096
        }
        
        # 发送请求到Silicon Flow API进行结构化解析
        structured_response = requests.post(SILICON_FLOW_API_URL, headers=headers, json=structured_payload)
        
        if structured_response.status_code != 200:
            logger.warning(f"结构化解析请求失败: {structured_response.status_code} - {structured_response.text}")
            # 如果结构化解析失败，返回原始文本结果
            return JSONResponse(content={
                "text": text_content,
                "status": "success"
            })
        
        # 解析结构化响应
        structured_result = structured_response.json()
        structured_content = structured_result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # 尝试解析返回的JSON字符串
        try:
            # 移除可能存在的markdown代码块标记
            if structured_content.startswith("```json"):
                structured_content = structured_content.replace("```json", "", 1)
            if structured_content.endswith("```"):
                structured_content = structured_content.rsplit("```", 1)[0]
            
            structured_content = structured_content.strip()
            parsed_json = json.loads(structured_content)
            
            # 构建StructuredOCR响应
            file_name = file.filename or "uploaded_image"
            structured_ocr_response = StructuredOCR(
                file_name=file_name,
                topics=topics or [],
                languages=languages,
                ocr_contents=parsed_json
            )
            
            # 构建最终的响应格式
            final_response = {
                "result": 1,
                "response": {
                    "data": structured_ocr_response.dict(),
                    "id": os.urandom(16).hex(),
                    "message": "success"
                }
            }
            
            return JSONResponse(content=final_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            # 如果JSON解析失败，返回原始文本结果
            return JSONResponse(content={
                "text": text_content,
                "status": "success"
            })
        except Exception as e:
            logger.error(f"结构化处理失败: {str(e)}")
            # 如果处理失败，返回原始文本结果
            return JSONResponse(content={
                "text": text_content,
                "status": "success"
            })
    
    except Exception as e:
        logger.error(f"结构化OCR处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")