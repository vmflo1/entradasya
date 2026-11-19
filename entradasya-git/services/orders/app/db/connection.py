"""Conexión a la base de datos PROPIA del servicio y aplicación de migraciones.

Cada servicio solo conoce su propia base (requerimiento técnico 2).
"""
import logging
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from app.core.config import settings

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def _conninfo() -> str:
    return make_conninfo(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        connect_timeout=settings.db_connect_timeout,
        # Las fechas se devuelven en la zona horaria del evento (Bolivia, -04:00)
        options=f"-c TimeZone={settings.db_timezone}",
    )


@contextmanager
def get_conn():
    """Abre una conexión, hace commit al terminar o rollback si hubo error."""
    conn = psycopg.connect(_conninfo(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def run_migrations() -> None:
    """Ejecuta en orden los archivos .sql de la carpeta migrations/ (son idempotentes)."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    with get_conn() as conn:
        for f in files:
            log.info("Aplicando migración %s", f.name)
            conn.execute(f.read_text(encoding="utf-8"))
    log.info("Migraciones aplicadas: %d", len(files))


def db_ok() -> bool:
    try:
        with get_conn() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Sin conexión a la base de datos: %s", exc)
        return False
