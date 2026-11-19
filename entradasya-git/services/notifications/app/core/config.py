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

    internal_api_key: str

    # Servidor de correo (en la v1: Mailpit)
    mail_host: str
    mail_port: int
    mail_from: str
    mail_user: str = ""
    mail_password: str = ""
    mail_starttls: bool = False
    mail_timeout: float = 5.0


settings = Settings()
