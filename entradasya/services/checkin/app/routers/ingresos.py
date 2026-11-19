from fastapi import APIRouter, Depends

from app.core.security import require_roles
from app.schemas.ingresos import AsistentesOut, IngresoIn, IngresoOut
from app.services import ingresos

router = APIRouter(tags=["ingresos"])


@router.post("/ingresos", response_model=IngresoOut)
def registrar(data: IngresoIn, user: dict = Depends(require_roles("portero"))):
    """El portero escanea o escribe el código. Responde si el ingreso se permite o el motivo del rechazo."""
    return ingresos.registrar(user, data.codigo, data.evento_id)


@router.get("/eventos/{evento_id}/asistentes", response_model=AsistentesOut)
def asistentes(evento_id: int, _: dict = Depends(require_roles("portero", "organizador"))):
    """Cuántas personas ingresaron a un evento."""
    return ingresos.contar(evento_id)
