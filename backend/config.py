"""
VaultAI Configuration Module

This module provides the settings configuration for the VaultAI application.
All sensitive configuration values are loaded from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    OPENAI_API_KEY: str = ""
    
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    DATABASE_URL: str = "sqlite:///podcast.db"
    
    PAYSTACK_SECRET_KEY: str = ""
    
    APP_NAME: str = "VaultAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    STORAGE_PATH: str = "storage"
    
    CORS_ORIGINS: list[str] = ["*"]
    
    PLAN_LIMITS: dict = {
        "free": 3,
        "creator": 20,
        "studio": float("inf")
    }


settings = Settings()


def get_plan_limit(plan: str) -> int:
    return settings.PLAN_LIMITS.get(plan, 3)


def check_plan_limit(plan: str, current_count: int) -> bool:
    limit = get_plan_limit(plan)
    if limit == float("inf"):
        return True
    return current_count < limit