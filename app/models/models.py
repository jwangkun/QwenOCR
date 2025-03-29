from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class OCRResponse(BaseModel):
    text: str
    status: str

class StructuredOCR(BaseModel):
    file_name: str
    topics: List[str]
    languages: str
    ocr_contents: Dict[str, Any]

class JSONSchema(BaseModel):
    json_schema: Dict[str, Any]
    description: Optional[str] = "用户提供的JSON Schema"

class SchemaOCR(BaseModel):
    file_name: str
    json_schema: Dict[str, Any]
    ocr_contents: Dict[str, Any]

class ChatMessage(BaseModel):
    user: str
    assistant: str

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessage]
    status: str