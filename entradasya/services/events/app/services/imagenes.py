"""Imagen del evento: se sube una vez y se guardan dos versiones WebP en la carpeta local."""
import logging
import secrets
from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

log = logging.getLogger(__name__)

# (sufijo, ancho, alto): tarjeta 3:4 de la cartelera y banner 16:9 de la página del evento
VARIANTES = [("card", 840, 1120), ("banner", 1920, 1080)]


def procesar(evento_id: int, contenido: bytes) -> str:
    """Valida la imagen, genera las variantes y devuelve la clave para guardar en el evento."""
    if len(contenido) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"La imagen supera los {settings.max_image_mb} MB")
    try:
        img = Image.open(BytesIO(contenido))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo no es una imagen válida (JPG, PNG o WebP)")

    img = ImageOps.exif_transpose(img).convert("RGB")
    clave = f"evento-{evento_id}-{secrets.token_hex(4)}"
    carpeta = settings.images_path
    carpeta.mkdir(parents=True, exist_ok=True)
    for sufijo, ancho, alto in VARIANTES:
        variante = ImageOps.fit(img, (ancho, alto), method=Image.Resampling.LANCZOS)
        variante.save(carpeta / f"{clave}-{sufijo}.webp", "WEBP", quality=82, method=6)
    log.info("Imagen guardada para el evento %s: %s", evento_id, clave)
    return clave


def borrar(clave: str | None) -> None:
    if not clave:
        return
    for sufijo, _, _ in VARIANTES:
        (settings.images_path / f"{clave}-{sufijo}.webp").unlink(missing_ok=True)


def ruta(archivo: str):
    """Devuelve la ruta de un archivo de imagen, sin permitir salir de la carpeta."""
    if "/" in archivo or "\\" in archivo or not archivo.endswith(".webp"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no encontrada")
    p = settings.images_path / archivo
    if not p.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Imagen no encontrada")
    return p
