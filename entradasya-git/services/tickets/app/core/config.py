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

    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # Carpeta local donde se guardan los PDF (relativa a la carpeta del servicio o absoluta)
    tickets_dir: str

    @property
    def tickets_path(self) -> Path:
        p = Path(self.tickets_dir)
        return p if p.is_absolute() else (SERVICE_DIR / p).resolve()


settings = Settings()
