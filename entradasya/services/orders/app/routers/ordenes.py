from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.security import get_current_user, require_roles
from app.schemas.ordenes import CompraIn, OrdenOut, VentasOut
from app.services import ordenes, ventas

router = APIRouter(tags=["ordenes"])


@router.post("/ordenes", response_model=OrdenOut, status_code=status.HTTP_201_CREATED)
def comprar(data: CompraIn, user: dict = Depends(get_current_user)):
    return ordenes.crear_compra(user, data)


@router.get("/ordenes/mias", response_model=list[OrdenOut])
def historial(user: dict = Depends(get_current_user)):
    return ordenes.mis_ordenes(user["id"])


@router.get("/ordenes/{orden_id}", response_model=OrdenOut)
def detalle(orden_id: UUID, user: dict = Depends(get_current_user)):
    return ordenes.obtener(orden_id, user["id"])


@router.get("/ventas/eventos/{evento_id}", response_model=VentasOut)
def ventas_evento(evento_id: int, user: dict = Depends(require_roles("organizador"))):
    """Ventas e ingresos de un evento. Solo su organizador puede verlas."""
    return ventas.resumen(user, evento_id)
