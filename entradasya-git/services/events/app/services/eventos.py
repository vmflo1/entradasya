import logging

from fastapi import HTTPException, status

from app.db.connection import get_conn

log = logging.getLogger(__name__)


def estado_venta(disponible: int, total: int) -> str:
    if disponible <= 0:
        return "Agotado"
    if disponible <= max(10, total * 0.1):
        return "Pocas entradas"
    return "Disponible"


def listar_publicados() -> list[dict]:
    """Solo los eventos publicados aparecen en la cartelera."""
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT e.id, e.nombre, e.fecha, e.lugar, e.imagen, e.descripcion,
                   MIN(s.precio)                       AS precio_desde,
                   COALESCE(SUM(s.cupo_disponible), 0) AS cupo_disponible,
                   COALESCE(SUM(s.cupo_total), 0)      AS cupo_total
            FROM eventos e
            LEFT JOIN sectores s ON s.evento_id = e.id
            WHERE e.estado = 'publicado'
            GROUP BY e.id
            ORDER BY e.fecha
            """
        ).fetchall()
    for r in rows:
        r["vendidos"] = r["cupo_total"] - r["cupo_disponible"]
        r["estado_venta"] = estado_venta(r["cupo_disponible"], r["cupo_total"])
    return rows


def obtener_publicado(evento_id: int) -> dict:
    with get_conn() as conn:
        evento = conn.execute(
            """
            SELECT id, nombre, fecha, lugar, imagen, descripcion, estado
            FROM eventos WHERE id = %s AND estado = 'publicado'
            """,
            (evento_id,),
        ).fetchone()
        if evento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
        sectores = conn.execute(
            """
            SELECT id, nombre, precio, cupo_total, cupo_disponible
            FROM sectores WHERE evento_id = %s ORDER BY precio DESC
            """,
            (evento_id,),
        ).fetchall()
    for s in sectores:
        s["estado_venta"] = estado_venta(s["cupo_disponible"], s["cupo_total"])
    evento["sectores"] = sectores
    evento["estado_venta"] = estado_venta(
        sum(s["cupo_disponible"] for s in sectores), sum(s["cupo_total"] for s in sectores)
    )
    return evento


def _respuesta_reserva(conn, reserva: dict) -> dict:
    datos = conn.execute(
        """
        SELECT s.nombre AS sector_nombre, s.precio,
               e.id AS evento_id, e.nombre, e.fecha, e.lugar
        FROM sectores s JOIN eventos e ON e.id = s.evento_id
        WHERE s.id = %s
        """,
        (reserva["sector_id"],),
    ).fetchone()
    return {
        "orden_id": reserva["orden_id"],
        "sector_id": reserva["sector_id"],
        "sector_nombre": datos["sector_nombre"],
        "cantidad": reserva["cantidad"],
        "precio_unitario": datos["precio"],
        "total": datos["precio"] * reserva["cantidad"],
        "evento": {
            "id": datos["evento_id"],
            "nombre": datos["nombre"],
            "fecha": datos["fecha"],
            "lugar": datos["lugar"],
        },
    }


def reservar(orden_id: str, evento_id: int, sector_id: int, cantidad: int) -> dict:
    """Reserva cupos de forma atómica: nunca se vende más que el cupo disponible."""
    with get_conn() as conn:
        existente = conn.execute(
            "SELECT orden_id, sector_id, cantidad, estado FROM reservas WHERE orden_id = %s",
            (orden_id,),
        ).fetchone()
        if existente:
            if existente["estado"] == "liberada":
                raise HTTPException(status.HTTP_409_CONFLICT, "La reserva de esta orden ya fue liberada")
            return _respuesta_reserva(conn, existente)  # misma solicitud repetida

        evento = conn.execute(
            "SELECT id FROM eventos WHERE id = %s AND estado = 'publicado'", (evento_id,)
        ).fetchone()
        if evento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado o no publicado")

        # El UPDATE con la condición "cupo_disponible >= cantidad" es atómico en PostgreSQL:
        # si dos compras llegan a la vez, solo una puede descontar el último cupo.
        sector = conn.execute(
            """
            UPDATE sectores
            SET cupo_disponible = cupo_disponible - %s
            WHERE id = %s AND evento_id = %s AND cupo_disponible >= %s
            RETURNING id
            """,
            (cantidad, sector_id, evento_id, cantidad),
        ).fetchone()
        if sector is None:
            existe = conn.execute(
                "SELECT 1 FROM sectores WHERE id = %s AND evento_id = %s", (sector_id, evento_id)
            ).fetchone()
            if existe is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Sector no encontrado")
            log.info("Sin cupo: orden=%s sector=%s cantidad=%s", orden_id, sector_id, cantidad)
            raise HTTPException(status.HTTP_409_CONFLICT, "Agotado")

        reserva = conn.execute(
            """
            INSERT INTO reservas (orden_id, evento_id, sector_id, cantidad)
            VALUES (%s, %s, %s, %s)
            RETURNING orden_id, sector_id, cantidad
            """,
            (orden_id, evento_id, sector_id, cantidad),
        ).fetchone()
        log.info("Cupos reservados: orden=%s sector=%s cantidad=%s", orden_id, sector_id, cantidad)
        return _respuesta_reserva(conn, reserva)


def liberar(orden_id: str) -> bool:
    """Devuelve los cupos de una reserva. Si ya estaba liberada, no hace nada."""
    with get_conn() as conn:
        reserva = conn.execute(
            """
            UPDATE reservas SET estado = 'liberada', liberada_en = now()
            WHERE orden_id = %s AND estado = 'reservada'
            RETURNING sector_id, cantidad
            """,
            (orden_id,),
        ).fetchone()
        if reserva is None:
            return False
        conn.execute(
            "UPDATE sectores SET cupo_disponible = cupo_disponible + %s WHERE id = %s",
            (reserva["cantidad"], reserva["sector_id"]),
        )
    log.info("Cupos liberados: orden=%s cantidad=%s", orden_id, reserva["cantidad"])
    return True
