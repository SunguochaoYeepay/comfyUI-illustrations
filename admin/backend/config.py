from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    app_name: str = "YeePay Admin"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./admin.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    COMFYUI_MODELS_DIR: Path = Path(os.getenv("COMFYUI_MODELS_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/models"))
    COMFYUI_LORAS_DIR: Path = Path(os.getenv("COMFYUI_LORAS_DIR", "E:/AI-Image/ComfyUI-aki-v1.4/models/loras"))
    YEEPAY_MODELS_DIR: Path = Path(os.getenv("YEEPAY_MODELS_DIR", "E:/AI-Image/YeePay/back/models"))
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8888"))
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:9000")

    class Config:
        env_file = ".env"

settings = Settings()