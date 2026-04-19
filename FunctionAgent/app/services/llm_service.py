# -*- coding: utf-8 -*-
"""LLM 多 Provider 服务"""
import logging
from typing import List, Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod
from app.config import settings

logger = logging.getLogger(__name__)


class BaseLLMService(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], tools: Optional[List] = None,
             tool_choice: Optional[str] = None) -> Dict[str, Any]: pass

    @abstractmethod
    def chat_simple(self, prompt: str) -> str: pass


class DashScopeService(BaseLLMService):
    def __init__(self, api_key: str = "", model: str = "", temperature: float = 0.3,
                 max_tokens: int = 2048):
        import dashscope
        from dashscope import Generation
        dashscope.api_key = api_key or settings.dashscope_api_key
        self.model = model or settings.llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.Generation = Generation

    def chat(self, messages: List[Dict], tools: Optional[List] = None,
             tool_choice: Optional[str] = None) -> Dict[str, Any]:
        kwargs = dict(
            model=self.model, messages=messages, stream=False,
            result_format="message", temperature=self.temperature, max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        resp = self.Generation.call(**kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f"DashScope API 错误 {resp.status_code}: {getattr(resp, 'message', resp)}")
        msg = resp.output.choices[0].message
        result = {"content": msg.content or "", "tool_calls": []}
        try:
            tc_list = msg.tool_calls
            if tc_list:
                for tc in tc_list:
                    # DashScope 返回 dict，兼容 SDK 对象
                    if isinstance(tc, dict):
                        fn = tc.get("function", {})
                        result["tool_calls"].append({
                            "id": tc.get("id", ""),
                            "name": fn.get("name", "") if isinstance(fn, dict) else getattr(fn, "name", ""),
                            "arguments": fn.get("arguments", "{}") if isinstance(fn, dict) else getattr(fn, "arguments", "{}"),
                        })
                    else:
                        result["tool_calls"].append({
                            "id": getattr(tc, "id", ""),
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        })
        except (KeyError, AttributeError):
            pass
        return result

    def chat_simple(self, prompt: str) -> str:
        return self.chat([{"role": "user", "content": prompt}])["content"]


class OpenAIService(BaseLLMService):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = "",
                 temperature: float = 0.3, max_tokens: int = 2048):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key or settings.openai_api_key,
            base_url=base_url or settings.openai_base_url,
        )
        self.model = model or settings.llm_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(self, messages: List[Dict], tools: Optional[List] = None,
             tool_choice: Optional[str] = None) -> Dict[str, Any]:
        kwargs = dict(model=self.model, messages=messages, stream=False,
                      temperature=self.temperature, max_tokens=self.max_tokens)
        if tools:
            kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        result = {"content": msg.content or "", "tool_calls": []}
        if msg.tool_calls:
            result["tool_calls"] = [
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in msg.tool_calls
            ]
        return result

    def chat_simple(self, prompt: str) -> str:
        return self.chat([{"role": "user", "content": prompt}])["content"]


def create_llm_service(provider: Optional[str] = None) -> BaseLLMService:
    p = provider or settings.llm_provider
    if p == "dashscope":
        return DashScopeService()
    elif p == "openai":
        return OpenAIService()
    elif p == "ollama":
        from openai import OpenAI
        return OpenAIService(api_key="ollama", base_url="http://localhost:11434/v1", model="qwen2.5:7b")
    else:
        raise ValueError(f"不支持的 LLM Provider: {p}")
