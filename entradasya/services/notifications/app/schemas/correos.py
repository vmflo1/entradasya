from decimal import Decimal

from pydantic import BaseModel, Field


class ConfirmacionIn(BaseModel):
    email: str = Field(max_length=255)
    nombre: str = Field(max_length=100)
    orden_id: str
    evento_nombre: str
    evento_fecha: str          # ya formateada por quien llama
    evento_lugar: str
    sector_nombre: str
    cantidad: int
    total: Decimal
    enlace: str                # enlace a "Mis entradas" en la web


class EnvioOut(BaseModel):
    enviado: bool
    destinatario: str
