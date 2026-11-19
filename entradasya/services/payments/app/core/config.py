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

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_connect_timeout: int = 5
    db_timezone: str = "America/La_Paz"

    internal_api_key: str
    # Regla fija de la pasarela simulada: tarjetas que terminan así se rechazan
    reject_suffix: str = "0000"


settings = Settings()
