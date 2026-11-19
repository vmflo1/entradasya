"""Flujo de compra: orders coordina, en orden, a events, payments, tickets y notifications."""
import logging
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.core.config import settings
from app.db.connection import get_conn
from app.services import clientes

log = logging.getLogger(__name__)

COLUMNAS = """id, evento_id, sector_id, cantidad, precio_unitario, total, evento_nombre,
              evento_fecha, evento_lugar, sector_nombre, estado, motivo,
              entradas_emitidas, correo_enviado, creado_en"""

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_texto(fecha: datetime) -> str:
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}, {fecha:%H:%M}"


def _actualizar(orden_id: str, **campos) -> dict:
    sets = ", ".join(f"{k} = %s" for k in campos)
    with get_conn() as conn:
        return conn.execute(
            f"UPDATE ordenes SET {sets}, actualizado_en = now() WHERE id = %s RETURNING {COLUMNAS}",
            (*campos.values(), orden_id),
        ).fetchone()


def crear_compra(user: dict, compra) -> dict:
    token = user["token"]
    orden_id = str(uuid4())

    # 1. La orden nace en estado "pendiente"
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ordenes (id, usuario_id, email, evento_id, sector_id, cantidad)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (orden_id, user["id"], user["email"], compra.evento_id, compra.sector_id, compra.cantidad),
        )
    log.info("Orden %s creada (pendiente) usuario=%s", orden_id, user["id"])

    # 2. events reserva los cupos
    try:
        reserva = clientes.reservar_cupos(token, orden_id, compra.evento_id, compra.sector_id, compra.cantidad)
    except clientes.Agotado:
        _actualizar(orden_id, estado="cancelada", motivo="Agotado")
        raise HTTPException(status.HTTP_409_CONFLICT, "Agotado")
    except clientes.ServicioError as exc:
        _actualizar(orden_id, estado="cancelada", motivo=str(exc))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"No se pudo reservar: {exc.mensaje}")

    evento = reserva["evento"]
    evento_fecha = datetime.fromisoformat(evento["fecha"])
    _actualizar(
        orden_id,
        precio_unitario=reserva["precio_unitario"],
        total=reserva["total"],
        evento_nombre=evento["nombre"],
        evento_fecha=evento_fecha,
        evento_lugar=evento["lugar"],
        sector_nombre=reserva["sector_nombre"],
    )

    # 3. payments cobra. Si rechaza, events libera los cupos
    try:
        pago = clientes.cobrar(orden_id, str(reserva["total"]), compra.metodo, compra.tarjeta_numero)
    except clientes.ServicioError as exc:
        clientes.liberar_cupos(token, orden_id)
        _actualizar(orden_id, estado="rechazada", motivo=str(exc))
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "El servicio de pagos no está disponible")

    if pago["resultado"] != "aprobado":
        clientes.liberar_cupos(token, orden_id)
        _actualizar(orden_id, estado="rechazada", motivo=pago.get("motivo") or "Pago rechazado")
        log.info("Orden %s rechazada por el pago", orden_id)
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Pago rechazado")

    orden = _actualizar(orden_id, estado="pagada")
    log.info("Orden %s pagada", orden_id)

    # 4. tickets genera las entradas (PDF + QR)
    try:
        clientes.generar_entradas(token, {
            "orden_id": orden_id,
            "evento_id": evento["id"],
            "evento_nombre": evento["nombre"],
            "evento_fecha": evento["fecha"],
            "evento_lugar": evento["lugar"],
            "sector_nombre": reserva["sector_nombre"],
            "cantidad": compra.cantidad,
        })
        orden = _actualizar(orden_id, entradas_emitidas=True)
    except clientes.ServicioError as exc:
        # La orden ya está pagada: queda registrada y las entradas se pueden regenerar
        log.error("Orden %s pagada pero sin entradas: %s", orden_id, exc)

    # 5. notifications envía el correo. Si falla, la compra sigue siendo válida
    try:
        clientes.enviar_confirmacion({
            "email": user["email"],
            "nombre": user.get("nombre") or "",
            "orden_id": orden_id,
            "evento_nombre": evento["nombre"],
            "evento_fecha": _fecha_texto(evento_fecha),
            "evento_lugar": evento["lugar"],
            "sector_nombre": reserva["sector_nombre"],
            "cantidad": compra.cantidad,
            "total": str(reserva["total"]),
            "enlace": f"{settings.public_url.rstrip('/')}/mis-entradas",
        })
        orden = _actualizar(orden_id, correo_enviado=True)
    except clientes.ServicioError as exc:
        log.warning("Orden %s: no se envió el correo (%s). La compra sigue siendo válida", orden_id, exc)

    return orden


def mis_ordenes(usuario_id: int) -> list[dict]:
    with get_conn() as conn:
        return conn.execute(
            f"SELECT {COLUMNAS} FROM ordenes WHERE usuario_id = %s ORDER BY creado_en DESC",
            (usuario_id,),
        ).fetchall()


def obtener(orden_id: UUID, usuario_id: int) -> dict:
    with get_conn() as conn:
        fila = conn.execute(
            f"SELECT {COLUMNAS} FROM ordenes WHERE id = %s AND usuario_id = %s",
            (str(orden_id), usuario_id),
        ).fetchone()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
    return fila
