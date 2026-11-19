"""Genera la imagen del código QR de una entrada."""
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_Q


def generar_qr_png(contenido: str) -> BytesIO:
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_Q, box_size=10, border=1)
    qr.add_data(contenido)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#111111", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
