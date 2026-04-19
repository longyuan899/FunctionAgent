# -*- coding: utf-8 -*-
"""ReAct Agent — 核心任务编排引擎"""
import time
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from app.config import settings
from app.services.llm_service import create_llm_service
from app.services.session_manager import session_store

logger = logging.getLogger(__name__)

MAX_TURNS = 8   # 最大工具调用轮次，防止无限循环
DEFAULT_SYSTEM_PROMPT = """你是一个企业智能助手，可以调用各种工具完成用户任务。

可用工具：calendar_query, calendar_create, calendar_check_conflict,
web_search, weather_query, unit_convert,
db_query, db_schema, room_search, room_book

调用工具的规则：
1. 当用户询问天气、日程、会议等信息时，先调用相应工具获取真实数据
2. 用户问数据库问题（员工/订单/产品）时，先调用 db_schema 了解表结构，再调用 db_query
3. 预约会议室时，先查询 room_search 找可用会议室，再调用 room_book 完成预约
4. 工具执行后，结合结果回答用户，不要重复调用相同工具
5. 如果用户意图不明确，先调用工具获取信息再追问

回复格式：
- 工具调用后：直接展示工具结果即可
- 最终回答：简洁明了，基于工具返回的真实数据"""
# 不需要工具时直接回答，不需要调用任何工具


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str
    result: Optional[str] = None
    success: bool = True


@dataclass
class AgentTurn:
    user_message: str
    assistant_content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    final_answer: str = ""


class FunctionAgent:
    """Function Calling 智能代理"""

    def __init__(self, session_id: str, tools: List[dict]):
        self.session_id = session_id
        self.tools = tools
        self.llm = create_llm_service()
        self._tool_registry = None

    def _get_tool_registry(self):
        if self._tool_registry is None:
            from app.tools.base import registry
            self._tool_registry = registry
        return self._tool_registry

    def chat(self, user_message: str, stream: bool = False) -> Dict[str, Any]:
        """单轮对话，返回回答"""
        start = time.time()

        # 获取历史消息
        history = session_store.get_messages(self.session_id, max_turns=10)

        # 构建 LLM 消息列表
        messages = [{"role": "system", "content": DEFAULT_SYSTEM_PROMPT}]
        for m in history:
            messages.append({"role": "user", "content": m["content"]})
            if m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {"name": tc["name"], "arguments": tc["arguments"]}
                            }
                        ]
                    })
                    if tc.get("result"):
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": str(tc["result"]),
                        })
        messages.append({"role": "user", "content": user_message})

        # 记录本次调用
        tool_calls_record: List[Dict] = []
        turns = 0
        final_content = ""
        pending_tool_calls = []

        while turns < MAX_TURNS:
            turns += 1

            # 调用 LLM（带 tools）
            resp = self.llm.chat(messages, tools=self.tools)
            content = resp.get("content", "").strip()
            tool_calls = resp.get("tool_calls", [])

            if not tool_calls:
                # 无工具调用，直接回答
                final_content = content
                break

            # 有工具调用，执行它们
            pending_tool_calls = tool_calls
            registry = self._get_tool_registry()

            for tc in tool_calls:
                tool_id = tc["id"]
                tool_name = tc["name"]
                raw_args = tc.get("arguments", "{}")
                if isinstance(raw_args, str):
                    try:
                        arguments = json.loads(raw_args)
                    except json.JSONDecodeError:
                        arguments = {}
                else:
                    arguments = raw_args

                logger.info(f"[Agent] 调用工具: {tool_name}({arguments})")

                # 执行工具
                tool_result = registry.execute(tool_name, arguments)
                result_str = json.dumps(tool_result, ensure_ascii=False, default=str)

                tool_calls_record.append({
                    "id": tool_id, "name": tool_name,
                    "arguments": raw_args if isinstance(raw_args, str) else json.dumps(arguments),
                    "result": result_str, "success": tool_result.success,
                })

                # 追加 tool 消息供 LLM 继续推理
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": result_str,
                })

                if not tool_result.success:
                    logger.warning(f"[Agent] 工具 {tool_name} 失败: {tool_result.error}")

            # 检查是否还有新工具调用（LLM 根据结果继续推理）
            if turns >= MAX_TURNS:
                final_content = content or "已执行完所有工具调用，抱歉未能给出完整回答"
                break

        # 如果没有任何内容，让 LLM 总结一下
        if not final_content and pending_tool_calls:
            summary_resp = self.llm.chat(messages, tools=None)
            final_content = summary_resp.get("content", "").strip()

        if not final_content:
            final_content = "抱歉，暂时无法回答这个问题。"

        elapsed = (time.time() - start) * 1000

        return {
            "reply": final_content,
            "tool_calls": tool_calls_record,
            "turns": turns,
            "elapsed_ms": round(elapsed, 1),
        }

    def chat_stream(self, user_message: str):
        """流式返回（先生成回答）"""
        result = self.chat(user_message, stream=False)
        return result


def get_agent_tools() -> List[dict]:
    """获取所有注册工具的 schema"""
    from app.tools.base import registry
    return registry.list_all()


def create_agent(session_id: str) -> FunctionAgent:
    tools = get_agent_tools()
    return FunctionAgent(session_id, tools)
