"""Ventas e ingresos de un evento, solo para su organizador."""
from fastapi import HTTPException, status

from app.db.connection import get_conn
from app.services import clientes


def resumen(user: dict, evento_id: int) -> dict:
    # orders no sabe de quién es cada evento: se lo pregunta a events
    try:
        evento = clientes.evento_del_organizador(user["token"], evento_id)
    except clientes.NoEsDueno:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    except clientes.ServicioError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"No se pudo verificar el evento: {exc.mensaje}")

    with get_conn() as conn:
        por_sector = conn.execute(
            """
            SELECT sector_nombre AS sector, SUM(cantidad)::int AS entradas, SUM(total) AS recaudado
            FROM ordenes WHERE evento_id = %s AND estado = 'pagada'
            GROUP BY sector_nombre ORDER BY recaudado DESC
            """,
            (evento_id,),
        ).fetchall()
        conteo = conn.execute(
            """
            SELECT COUNT(*) FILTER (WHERE estado = 'pagada')    AS pagadas,
                   COUNT(*) FILTER (WHERE estado = 'rechazada') AS rechazadas
            FROM ordenes WHERE evento_id = %s
            """,
            (evento_id,),
        ).fetchone()
    return {
        "evento_id": evento_id,
        "evento_nombre": evento["nombre"],
        "entradas_vendidas": sum(s["entradas"] for s in por_sector),
        "ordenes_pagadas": conteo["pagadas"],
        "ordenes_rechazadas": conteo["rechazadas"],
        "total_recaudado": sum((s["recaudado"] for s in por_sector), 0),
        "por_sector": por_sector,
    }
