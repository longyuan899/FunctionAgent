# -*- coding: utf-8 -*-
"""全局配置"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "智能任务代理系统"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8001
    debug: bool = True
    log_level: str = "INFO"

    # LLM 配置
    llm_provider: str = "dashscope"   # dashscope / openai / ollama
    dashscope_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "qwen-plus"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048

    # Redis 会话存储
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_ttl: int = 3600       # 会话过期秒数
    use_redis: bool = False     # False 时自动回退到内存存储

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def init_dirs(self):
        Path("data").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)


settings = Settings()
settings.init_dirs()
