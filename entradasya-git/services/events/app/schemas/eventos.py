from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SectorOut(BaseModel):
    id: int
    nombre: str
    precio: Decimal
    cupo_total: int
    cupo_disponible: int
    estado_venta: str


class EventoResumenOut(BaseModel):
    id: int
    nombre: str
    fecha: datetime
    lugar: str
    imagen: str | None
    descripcion: str
    precio_desde: Decimal | None
    cupo_disponible: int
    cupo_total: int
    vendidos: int
    estado_venta: str


class EventoDetalleOut(BaseModel):
    id: int
    nombre: str
    fecha: datetime
    lugar: str
    imagen: str | None
    descripcion: str
    estado: str
    estado_venta: str
    sectores: list[SectorOut]


class ReservaIn(BaseModel):
    orden_id: str = Field(min_length=1, max_length=64)
    evento_id: int
    sector_id: int
    cantidad: int = Field(ge=1, le=6)


class EventoMini(BaseModel):
    id: int
    nombre: str
    fecha: datetime
    lugar: str


class ReservaOut(BaseModel):
    orden_id: str
    sector_id: int
    sector_nombre: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    evento: EventoMini


class LiberarOut(BaseModel):
    orden_id: str
    liberada: bool
