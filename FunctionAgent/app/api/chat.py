# -*- coding: utf-8 -*-
"""对话 API"""
import time
import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.core.agent import create_agent, get_agent_tools
from app.services.session_manager import session_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["对话"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息，触发 Agent 执行"""
    sid = request.session_id or session_store.create()
    session_store.add_message(sid, "user", request.message)

    agent = create_agent(sid)
    result = agent.chat(request.message)

    session_store.add_message(
        sid, "assistant", result["reply"],
        tool_calls=result.get("tool_calls", [])
    )

    return ChatResponse(
        session_id=sid,
        reply=result["reply"],
        tool_calls=result.get("tool_calls", []),
        finished=True,
        elapsed_ms=result.get("elapsed_ms", 0),
    )


@router.get("/tools")
async def list_tools():
    """列出所有可用工具"""
    from app.tools.base import registry
    return {
        "tools": registry.list_all(),
        "categories": registry.list_categories(),
    }


@router.get("/sessions")
async def list_sessions():
    return {"sessions": session_store.list_sessions()}


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    success = session_store.delete(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"success": True}


@router.delete("/sessions")
async def clear_all_sessions():
    count = session_store.clear_all()
    return {"success": True, "deleted": count}


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    msgs = session_store.get_messages(session_id, max_turns=50)
    return {"session_id": session_id, "history": msgs}
