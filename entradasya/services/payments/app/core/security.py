"""Servicio interno: solo acepta llamadas que traen la clave interna compartida.

Además, Nginx no lo expone hacia afuera, así que en la práctica solo orders lo llama.
"""
import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_internal_key(x_internal_key: str | None = Header(default=None)) -> None:
    if not x_internal_key or not hmac.compare_digest(x_internal_key, settings.internal_api_key):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Servicio interno: acceso no permitido")
