from datetime import datetime

from pydantic import BaseModel, Field


class GenerarIn(BaseModel):
    """orders envía todos los datos del evento: tickets no consulta a ningún otro servicio."""
    orden_id: str = Field(min_length=1, max_length=64)
    evento_id: int
    evento_nombre: str = Field(max_length=150)
    evento_fecha: datetime
    evento_lugar: str = Field(max_length=150)
    sector_nombre: str = Field(max_length=60)
    cantidad: int = Field(ge=1, le=6)


class EntradaOut(BaseModel):
    codigo: str
    orden_id: str
    numero: int
    total_orden: int
    evento_id: int
    evento_nombre: str
    evento_fecha: datetime
    evento_lugar: str
    sector_nombre: str
    estado: str
    creado_en: datetime


class ValidacionOut(BaseModel):
    codigo: str
    existe: bool
    evento_id: int | None = None
    evento_nombre: str | None = None
    sector_nombre: str | None = None
    pertenece_al_evento: bool | None = None
    pagada: bool = False
    valida: bool = False
    motivo: str | None = None
