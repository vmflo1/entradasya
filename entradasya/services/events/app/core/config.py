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

    # Carpeta local de las imágenes de los eventos (relativa a esta carpeta o absoluta)
    images_dir: str
    max_image_mb: int = 5

    @property
    def images_path(self) -> Path:
        p = Path(self.images_dir)
        return p if p.is_absolute() else (SERVICE_DIR / p).resolve()


settings = Settings()
