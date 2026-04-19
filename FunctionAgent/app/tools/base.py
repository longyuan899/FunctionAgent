# -*- coding: utf-8 -*-
"""工具基类 & 注册中心"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    name: str
    type: str = "string"
    description: str = ""
    required: bool = False
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class ToolResult:
    success: bool
    result: Any = None
    error: str = ""
    elapsed_ms: float = 0
    tool_name: str = ""


class BaseTool(ABC):
    """工具基类"""
    name: str = ""
    description: str = ""
    category: str = "general"
    parameters: List[ToolParameter] = []
    timeout_seconds: int = 10

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass

    def get_schema(self) -> dict:
        """返回 OpenAI 格式的 tool schema"""
        props = {}
        required = []
        for p in self.parameters:
            props[p.name] = {"type": p.type, "description": p.description}
            if p.enum:
                props[p.name]["enum"] = p.enum
            if p.default is not None:
                props[p.name]["default"] = p.default
            if p.required:
                required.append(p.name)
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": required,
                }
            }
        }

    def run(self, **kwargs) -> ToolResult:
        start = time.time()
        try:
            result = self.execute(**kwargs)
            elapsed = (time.time() - start) * 1000
            return ToolResult(success=True, result=result,
                             elapsed_ms=round(elapsed, 1), tool_name=self.name)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"工具 {self.name} 执行失败: {e}")
            return ToolResult(success=False, error=str(e),
                             elapsed_ms=round(elapsed, 1), tool_name=self.name)


class ToolRegistry:
    """全局工具注册中心"""
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"注册工具: {tool.name} [{tool.category}]")

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_all(self) -> List[dict]:
        return [t.get_schema() for t in self._tools.values()]

    def list_categories(self) -> Dict[str, List[str]]:
        cats: Dict[str, List[str]] = {}
        for t in self._tools.values():
            cats.setdefault(t.category, []).append(t.name)
        return cats

    def execute(self, name: str, arguments: Dict) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(success=False, error=f"未找到工具: {name}")
        return tool.run(**arguments)


registry = ToolRegistry()
