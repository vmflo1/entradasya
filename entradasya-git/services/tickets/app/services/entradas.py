import logging
import secrets

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation

from app.core.config import settings
from app.db.connection import get_conn
from app.services.pdf import crear_pdf_entrada

log = logging.getLogger(__name__)

COLUMNAS = """codigo, orden_id, numero, total_orden, evento_id, evento_nombre,
              evento_fecha, evento_lugar, sector_nombre, estado, creado_en"""


def _nuevo_codigo() -> str:
    # 10 caracteres hexadecimales: corto para escribirlo a mano en la puerta
    return "EY-" + secrets.token_hex(5).upper()


def generar(usuario_id: int, datos: dict) -> list[dict]:
    """Genera una entrada (con su PDF y QR) por cada asiento comprado.
    Si la orden ya tiene entradas, devuelve las mismas (solicitud repetida)."""
    with get_conn() as conn:
        existentes = conn.execute(
            f"SELECT {COLUMNAS} FROM entradas WHERE orden_id = %s ORDER BY numero",
            (datos["orden_id"],),
        ).fetchall()
        if existentes:
            return existentes

        carpeta = settings.tickets_path
        carpeta.mkdir(parents=True, exist_ok=True)
        creadas = []
        for numero in range(1, datos["cantidad"] + 1):
            for _ in range(5):  # reintenta si (muy raramente) el código se repite
                codigo = _nuevo_codigo()
                if not conn.execute("SELECT 1 FROM entradas WHERE codigo = %s", (codigo,)).fetchone():
                    break
            archivo = f"{codigo}.pdf"
            entrada = {**datos, "codigo": codigo, "numero": numero, "total_orden": datos["cantidad"]}
            crear_pdf_entrada(carpeta / archivo, entrada)
            try:
                fila = conn.execute(
                    f"""
                    INSERT INTO entradas (codigo, orden_id, usuario_id, numero, total_orden, evento_id,
                                          evento_nombre, evento_fecha, evento_lugar, sector_nombre, pdf_archivo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING {COLUMNAS}
                    """,
                    (codigo, datos["orden_id"], usuario_id, numero, datos["cantidad"], datos["evento_id"],
                     datos["evento_nombre"], datos["evento_fecha"], datos["evento_lugar"],
                     datos["sector_nombre"], archivo),
                ).fetchone()
            except UniqueViolation:
                raise HTTPException(status.HTTP_409_CONFLICT, "Las entradas de esta orden ya se están generando")
            creadas.append(fila)
    log.info("Entradas generadas: orden=%s cantidad=%s", datos["orden_id"], len(creadas))
    return creadas


def mis_entradas(usuario_id: int) -> list[dict]:
    with get_conn() as conn:
        return conn.execute(
            f"SELECT {COLUMNAS} FROM entradas WHERE usuario_id = %s ORDER BY creado_en DESC, numero",
            (usuario_id,),
        ).fetchall()


def ruta_pdf(codigo: str, usuario_id: int):
    with get_conn() as conn:
        fila = conn.execute(
            "SELECT pdf_archivo, usuario_id FROM entradas WHERE codigo = %s", (codigo,)
        ).fetchone()
    if fila is None or fila["usuario_id"] != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrada no encontrada")
    ruta = settings.tickets_path / fila["pdf_archivo"]
    if not ruta.exists():
        log.error("Falta el archivo PDF %s", ruta)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El PDF de esta entrada no está disponible")
    return ruta


def validar(codigo: str, evento_id: int | None) -> dict:
    """Informa si un código existe, a qué evento pertenece y si es válido (lo usará checkin)."""
    codigo = codigo.strip().upper()
    with get_conn() as conn:
        fila = conn.execute(
            # La conexión usa TimeZone=DB_TIMEZONE, así que ::date y CURRENT_DATE son días locales
            """SELECT codigo, evento_id, evento_nombre, sector_nombre, estado,
                      evento_fecha::date AS dia_evento, CURRENT_DATE AS hoy
               FROM entradas WHERE codigo = %s""",
            (codigo,),
        ).fetchone()
    if fila is None:
        return {"codigo": codigo, "existe": False, "motivo": "Código inválido"}
    pertenece = evento_id is None or fila["evento_id"] == evento_id
    # La entrada solo sirve el día del evento
    es_hoy = fila["dia_evento"] == fila["hoy"]
    # Las entradas solo se emiten cuando la orden ya está pagada
    valida = pertenece and fila["estado"] == "valida" and es_hoy
    motivo = None
    if not pertenece:
        motivo = "Entrada de otro evento"
    elif fila["estado"] != "valida":
        motivo = "Entrada anulada"
    elif fila["dia_evento"] > fila["hoy"]:
        motivo = f"El evento aún no es hoy: es el {fila['dia_evento']:%d/%m/%Y}"
    elif fila["dia_evento"] < fila["hoy"]:
        motivo = f"El evento ya pasó: fue el {fila['dia_evento']:%d/%m/%Y}"
    return {
        "codigo": codigo,
        "existe": True,
        "evento_id": fila["evento_id"],
        "evento_nombre": fila["evento_nombre"],
        "sector_nombre": fila["sector_nombre"],
        "pertenece_al_evento": pertenece,
        "pagada": True,
        "valida": valida,
        "motivo": motivo,
    }
