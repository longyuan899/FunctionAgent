# -*- coding: utf-8 -*-
"""FastAPI 应用工厂"""
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.api import chat

# 全局日志
_handler = logging.StreamHandler()
_handler.terminator = ""
_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s\n"))
try:
    _handler.stream.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
_log = logging.getLogger()
_log.addHandler(_handler)
_log.setLevel(settings.log_level)
_log.info("智能任务代理系统启动中...")

# 预加载工具注册
from app.tools import *  # noqa: F401,F403


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Function Calling 智能代理，支持日历、搜索、会议、数据库等工具",
    )
    app.include_router(chat.router)

    # 前端页面路由
    frontend = Path("frontend/templates")
    if frontend.exists():
        from fastapi.responses import HTMLResponse
        from fastapi import Request

        @app.get("/", response_class=HTMLResponse)
        async def index():
            return FileResponse(frontend / "index.html")

        @app.get("/chat", response_class=HTMLResponse)
        async def chat_page():
            return FileResponse(frontend / "chat.html")

        @app.get("/tools", response_class=HTMLResponse)
        async def tools_page():
            return FileResponse(frontend / "tools.html")

        @app.get("/history", response_class=HTMLResponse)
        async def history_page():
            return FileResponse(frontend / "history.html")

    return app
