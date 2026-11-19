from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    fecha: datetime
    lugar: str = Field(min_length=2, max_length=150)
    descripcion: str = Field(default="", max_length=2000)

    @field_validator("nombre", "lugar", "descripcion")
    @classmethod
    def limpiar(cls, v: str) -> str:
        return v.strip()


class SectorIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=60)
    precio: Decimal = Field(ge=0, le=100000, decimal_places=2)
    cupo_total: int = Field(ge=1, le=100000)

    @field_validator("nombre")
    @classmethod
    def limpiar(cls, v: str) -> str:
        return v.strip()


class EstadoIn(BaseModel):
    estado: Literal["borrador", "publicado", "cancelado"]


class SectorOrgOut(BaseModel):
    id: int
    nombre: str
    precio: Decimal
    cupo_total: int
    cupo_disponible: int
    vendidos: int


class EventoOrgOut(BaseModel):
    id: int
    nombre: str
    fecha: datetime
    lugar: str
    imagen: str | None
    descripcion: str
    estado: str
    cupo_total: int
    vendidos: int
    sectores: list[SectorOrgOut]
