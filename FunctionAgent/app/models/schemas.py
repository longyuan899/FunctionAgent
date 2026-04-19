# -*- coding: utf-8 -*-
"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ToolCall(BaseModel):
    """工具调用记录"""
    tool: str
    arguments: Dict[str, Any]
    result: Optional[Any] = None
    success: bool = True
    elapsed_ms: float = 0


class Message(BaseModel):
    role: str  # user / assistant / system
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[Dict[str, Any]] = []
    finished: bool = True
    elapsed_ms: float = 0


class SessionInfo(BaseModel):
    session_id: str
    message_count: int = 0
    created_at: str = ""
    last_active: str = ""


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str = "general"
