from fastapi import APIRouter, Depends

from app.core.security import require_internal_key
from app.schemas.pagos import PagoIn, PagoOut
from app.services import pagos

# Todas las rutas exigen la clave interna: solo orders puede llamar a este servicio
router = APIRouter(tags=["pagos"], dependencies=[Depends(require_internal_key)])


@router.post("/pagos", response_model=PagoOut)
def pagar(data: PagoIn):
    return pagos.procesar_pago(data.orden_id, data.monto, data.metodo, data.tarjeta_numero)


@router.get("/pagos/{orden_id}", response_model=PagoOut)
def consultar(orden_id: str):
    return pagos.obtener(orden_id)
