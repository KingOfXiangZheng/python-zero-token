from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")

    auth_file: str = Field(default=".auth.json", description="Auth file")
    default_provider: str = Field(default="deepseek", description="Default provider")

    chrome_user_data_dir: str = Field(
        default="C:\\tmp\\chrome-debug-1",
        description="Chrome user data directory for persistent login",
    )
    chrome_cdp_port: int = Field(default=9222, description="Chrome CDP port")
    auto_start_chrome: bool = Field(
        default=True, description="Auto start Chrome if not running"
    )
    chrome_headless: bool = Field(
        default=False, description="Run Chrome in headless mode (no GUI)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()

PROVIDER_CONFIGS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://chat.deepseek.com",
        "api_prefix": "/api/v0",
        "models": {
            "deepseek-chat": {
                "name": "DeepSeek V3",
                "context_window": 64000,
                "max_tokens": 8192,
            },
            "deepseek-reasoner": {
                "name": "DeepSeek R1",
                "context_window": 64000,
                "max_tokens": 8192,
                "reasoning": True,
            },
        },
    },
    "glm": {
        "name": "GLM",
        "base_url": "https://chatglm.cn",
        "api_prefix": "/chatglm/chat-api",
        "models": {
            "glm-4-plus": {
                "name": "GLM-4 Plus",
                "context_window": 128000,
                "max_tokens": 4096,
            },
            "glm-4": {"name": "GLM-4", "context_window": 128000, "max_tokens": 4096},
            "glm-4-think": {
                "name": "GLM-4 Think",
                "context_window": 128000,
                "max_tokens": 4096,
                "reasoning": True,
            },
        },
    },
    "kimi": {
        "name": "Kimi",
        "base_url": "https://kimi.moonshot.cn",
        "api_prefix": "/api",
        "models": {
            "kimi": {"name": "Kimi", "context_window": 128000, "max_tokens": 4096}
        },
    },
    "doubao": {
        "name": "豆包",
        "base_url": "https://www.doubao.com",
        "api_prefix": "/samantha/chat",
        "models": {
            "doubao-pro-4k": {
                "name": "豆包 Pro 4K",
                "context_window": 4000,
                "max_tokens": 2000,
            },
            "doubao-lite-4k": {
                "name": "豆包 Lite 4K",
                "context_window": 4000,
                "max_tokens": 2000,
            },
        },
    },
}
