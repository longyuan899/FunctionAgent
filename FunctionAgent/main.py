# -*- coding: utf-8 -*-
"""智能任务代理系统 — 启动入口"""
import uvicorn
from app import create_app
from app.config import settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
