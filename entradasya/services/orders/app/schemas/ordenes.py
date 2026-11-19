import re
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

from app.core.config import settings


class CompraIn(BaseModel):
    evento_id: int
    sector_id: int
    cantidad: int = Field(ge=1, le=6, description="Máximo 6 entradas por compra")
    metodo: Literal["tarjeta", "qr"] = "tarjeta"
    # Datos de la tarjeta (solo con metodo="tarjeta"). Se validan aquí; a payments solo va el número.
    tarjeta_titular: str | None = Field(default=None, max_length=100)
    tarjeta_numero: str | None = None
    tarjeta_vencimiento: str | None = Field(default=None, description="MM/AA")
    tarjeta_cvv: str | None = Field(default=None, description="Código de seguridad: no se guarda ni se reenvía")

    @model_validator(mode="after")
    def validar_tarjeta(self):
        if self.metodo == "qr":
            # Con QR no se usan datos de tarjeta
            self.tarjeta_titular = self.tarjeta_numero = self.tarjeta_vencimiento = self.tarjeta_cvv = None
            return self

        titular = (self.tarjeta_titular or "").strip()
        if len(titular) < 2:
            raise ValueError("Escribe el nombre del titular")
        self.tarjeta_titular = titular

        numero = (self.tarjeta_numero or "").replace(" ", "").replace("-", "")
        if not numero.isdigit() or not 12 <= len(numero) <= 19:
            raise ValueError("El número de tarjeta debe tener entre 12 y 19 dígitos")
        self.tarjeta_numero = numero

        venc = (self.tarjeta_vencimiento or "").replace(" ", "")
        if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", venc):
            raise ValueError("El vencimiento debe tener el formato MM/AA")
        mes, anio = int(venc[:2]), 2000 + int(venc[3:])
        hoy = datetime.now(ZoneInfo(settings.db_timezone))
        if (anio, mes) < (hoy.year, hoy.month):
            raise ValueError("La tarjeta está vencida")
        self.tarjeta_vencimiento = venc

        if not re.fullmatch(r"\d{3,4}", self.tarjeta_cvv or ""):
            raise ValueError("El código de seguridad (CVV) debe tener 3 o 4 dígitos")
        return self


class OrdenOut(BaseModel):
    id: UUID
    evento_id: int
    sector_id: int
    cantidad: int
    precio_unitario: Decimal | None
    total: Decimal | None
    evento_nombre: str | None
    evento_fecha: datetime | None
    evento_lugar: str | None
    sector_nombre: str | None
    estado: str
    motivo: str | None
    entradas_emitidas: bool
    correo_enviado: bool
    creado_en: datetime


class VentaSectorOut(BaseModel):
    sector: str
    entradas: int
    recaudado: Decimal


class VentasOut(BaseModel):
    evento_id: int
    evento_nombre: str
    entradas_vendidas: int
    ordenes_pagadas: int
    ordenes_rechazadas: int
    total_recaudado: Decimal
    por_sector: list[VentaSectorOut]
