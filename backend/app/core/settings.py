import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Antigravity Core"
    API_V1_STR: str = "/api/antigravity"
    OPENAI_ENABLED: bool = False
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
