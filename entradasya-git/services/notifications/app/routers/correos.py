import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import require_internal_key
from app.schemas.correos import ConfirmacionIn, EnvioOut
from app.services import mailer

log = logging.getLogger(__name__)

# Servicio interno: solo orders lo llama (con la clave interna)
router = APIRouter(tags=["correos"], dependencies=[Depends(require_internal_key)])


@router.post("/correos/confirmacion", response_model=EnvioOut)
def confirmacion(data: ConfirmacionIn):
    try:
        mailer.enviar_confirmacion(data.model_dump())
    except Exception as exc:  # noqa: BLE001
        log.error("No se pudo enviar el correo a %s: %s", data.email, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo enviar el correo")
    return EnvioOut(enviado=True, destinatario=data.email)
