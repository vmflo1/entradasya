from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class IngresoIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=64)
    evento_id: int

    @field_validator("codigo")
    @classmethod
    def normalizar(cls, v: str) -> str:
        return v.strip().upper()


class IngresoOut(BaseModel):
    permitido: bool
    codigo: str
    motivo: str | None = None
    evento_nombre: str | None = None
    sector_nombre: str | None = None
    ingresado_en: datetime | None = None      # hora de este ingreso (si se permitió)
    primer_ingreso: datetime | None = None    # hora del primer ingreso (si ya se había usado)
    asistentes: int


class SectorIngresosOut(BaseModel):
    sector: str
    ingresados: int


class AsistentesOut(BaseModel):
    evento_id: int
    asistentes: int
    rechazos: int
    por_sector: list[SectorIngresosOut]
