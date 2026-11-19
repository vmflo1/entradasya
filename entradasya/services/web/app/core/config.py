"""Configuración leída SOLO de variables de entorno (o del archivo .env del servicio)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVICE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=SERVICE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    service_name: str
    host: str
    port: int
    log_level: str = "INFO"
    app_name: str = "EntradasYa"


settings = Settings()
