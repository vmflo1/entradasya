"""Envío de correos por SMTP. En la v1 el servidor es Mailpit: no se envía nada real."""
import html
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path
from string import Template

from app.core.config import settings

log = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def _render(nombre_plantilla: str, datos: dict) -> str:
    plantilla = Template((TEMPLATES_DIR / nombre_plantilla).read_text(encoding="utf-8"))
    seguros = {k: html.escape(str(v)) for k, v in datos.items()}
    return plantilla.safe_substitute(seguros)


def _enviar(destinatario: str, asunto: str, texto: str, cuerpo_html: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg.set_content(texto)
    msg.add_alternative(cuerpo_html, subtype="html")

    with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=settings.mail_timeout) as smtp:
        if settings.mail_starttls:
            smtp.starttls()
        if settings.mail_user:
            smtp.login(settings.mail_user, settings.mail_password)
        smtp.send_message(msg)


def enviar_confirmacion(datos: dict) -> None:
    total = f"{datos['total']:.2f}"
    cuerpo_html = _render("confirmacion.html", {**datos, "total": total})
    texto = (
        f"Hola {datos['nombre']},\n\n"
        f"Tu compra para {datos['evento_nombre']} está confirmada.\n"
        f"Fecha: {datos['evento_fecha']}\nLugar: {datos['evento_lugar']}\n"
        f"Sector: {datos['sector_nombre']} · Entradas: {datos['cantidad']} · Total: Bs {total}\n\n"
        f"Descarga tus entradas aquí: {datos['enlace']}\n\nOrden {datos['orden_id']}\n"
    )
    _enviar(datos["email"], f"Tus entradas para {datos['evento_nombre']}", texto, cuerpo_html)
    log.info("Correo de confirmación enviado a %s (orden %s)", datos["email"], datos["orden_id"])


def smtp_ok() -> bool:
    try:
        with smtplib.SMTP(settings.mail_host, settings.mail_port, timeout=2) as smtp:
            smtp.noop()
        return True
    except Exception as exc:  # noqa: BLE001
        log.warning("Servidor de correo no disponible: %s", exc)
        return False
