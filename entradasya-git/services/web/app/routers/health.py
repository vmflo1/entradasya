"""Chequeo de salud. web no tiene base de datos: si responde, puede atender."""
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["salud"])


@router.get("/health")
def health():
    return {"status": "ok", "servicio": settings.service_name}
