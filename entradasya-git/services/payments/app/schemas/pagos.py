from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class PagoIn(BaseModel):
    orden_id: str = Field(min_length=1, max_length=64)
    monto: Decimal = Field(ge=0)
    metodo: Literal["tarjeta", "qr"] = "tarjeta"
    # Solo con tarjeta. El código de seguridad (CVV) nunca llega a este servicio.
    tarjeta_numero: str | None = None

    @field_validator("tarjeta_numero")
    @classmethod
    def solo_digitos(cls, v: str | None) -> str | None:
        if v is None:
            return v
        limpio = v.replace(" ", "").replace("-", "")
        if not limpio.isdigit() or not 12 <= len(limpio) <= 19:
            raise ValueError("El número de tarjeta debe tener entre 12 y 19 dígitos")
        return limpio

    @model_validator(mode="after")
    def tarjeta_si_corresponde(self):
        if self.metodo == "tarjeta" and not self.tarjeta_numero:
            raise ValueError("Falta el número de tarjeta")
        return self


class PagoOut(BaseModel):
    orden_id: str
    monto: Decimal
    metodo: str
    tarjeta_ultimos4: str | None
    resultado: str
    motivo: str | None
    creado_en: datetime
