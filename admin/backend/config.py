from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "YeePay Admin"
    DATABASE_URL: str = "sqlite:///../admin.db"
    SECRET_KEY: str = "a_very_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COMFYUI_MODELS_DIR: Path = "E:/AI-Image/ComfyUI-aki-v1.4/models"
    COMFYUI_LORAS_DIR: Path = "E:/AI-Image/ComfyUI-aki-v1.4/models/loras"
    YEEPAY_MODELS_DIR: Path = "e:\\AI-Image\\YeePay\\back\\models"

    class Config:
        env_file = ".env"

settings = Settings()