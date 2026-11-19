import logging
from decimal import Decimal

from fastapi import HTTPException, status

from app.core.config import settings
from app.db.connection import get_conn

log = logging.getLogger(__name__)

COLUMNAS = "orden_id, monto, metodo, tarjeta_ultimos4, resultado, motivo, creado_en"


def procesar_pago(orden_id: str, monto: Decimal, metodo: str, tarjeta_numero: str | None) -> dict:
    """Aprueba o rechaza según una regla fija y nunca cobra dos veces la misma orden.

    Reglas fijas de la pasarela simulada:
      - tarjeta: se rechaza si termina en REJECT_SUFFIX (0000); si no, se aprueba.
      - qr: el cliente confirma que pagó desde la app de su banco; se aprueba.
    """
    ultimos4 = tarjeta_numero[-4:] if metodo == "tarjeta" else None
    if metodo == "tarjeta" and tarjeta_numero.endswith(settings.reject_suffix):
        resultado, motivo = "rechazado", "Tarjeta rechazada por el banco emisor"
    else:
        resultado, motivo = "aprobado", None

    with get_conn() as conn:
        # Si la orden ya tiene transacción, ON CONFLICT no inserta nada
        nueva = conn.execute(
            f"""
            INSERT INTO transacciones (orden_id, monto, metodo, tarjeta_ultimos4, resultado, motivo)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (orden_id) DO NOTHING
            RETURNING {COLUMNAS}
            """,
            (orden_id, monto, metodo, ultimos4, resultado, motivo),
        ).fetchone()
        if nueva:
            log.info("Pago %s: orden=%s monto=%s metodo=%s", resultado, orden_id, monto, metodo)
            return nueva

        existente = conn.execute(
            f"SELECT {COLUMNAS} FROM transacciones WHERE orden_id = %s", (orden_id,)
        ).fetchone()
    log.info("Solicitud repetida para la orden %s: se devuelve el resultado anterior", orden_id)
    return existente


def obtener(orden_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            f"SELECT {COLUMNAS} FROM transacciones WHERE orden_id = %s", (orden_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No hay pago para esa orden")
    return row
