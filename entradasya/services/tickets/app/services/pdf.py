"""Arma el PDF de una entrada: A6 vertical (105 x 148 mm) con el diseño de la marca.

Usa ReportLab porque se instala con pip en Windows y Linux sin dependencias extra.
Usa una sola familia tipográfica: Helvetica (incluida en ReportLab).
"""
import logging
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

from app.services import logo_marca
from app.services.qr import generar_qr_png

log = logging.getLogger(__name__)

FONDO = HexColor("#F2F0EB")
NEGRO = HexColor("#111111")
GRIS = HexColor("#8A8A8A")
BORDE = HexColor("#E2DFD8")
BLANCO = HexColor("#FFFFFF")
# Colores de énfasis: los mismos tres boletos del logo
AZUL = HexColor("#2B90A8")
AMARILLO = HexColor("#FAAC43")
ROJO = HexColor("#F5604F")

_NUM = re.compile(r"[MLCZ]|-?[0-9.]+")


def _trazo(c: canvas.Canvas, d: str):
    """Convierte un trazo SVG (solo M, L, C y Z absolutos) en un trazo de ReportLab."""
    p = c.beginPath()
    t = _NUM.findall(d)
    i = 0
    while i < len(t):
        cmd = t[i]
        if cmd == "Z":
            p.close()
            i += 1
            continue
        if cmd in "ML":
            x, y = float(t[i + 1]), float(t[i + 2])
            (p.moveTo if cmd == "M" else p.lineTo)(x, y)
            i += 3
        elif cmd == "C":
            v = [float(n) for n in t[i + 1:i + 7]]
            p.curveTo(*v)
            i += 7
        else:  # par de coordenadas extra después de L
            p.lineTo(float(t[i]), float(t[i + 1]))
            i += 2
    return p


def _logo(c: canvas.Canvas, x: float, y: float, alto: float, color_texto) -> None:
    """Dibuja el logo oficial con su esquina inferior izquierda en (x, y)."""
    bx, by, bw, bh = logo_marca.CAJA
    escala = alto / bh
    c.saveState()
    c.translate(x, y + alto)
    c.scale(escala, -escala)          # los trazos SVG tienen el eje Y hacia abajo
    c.translate(-bx, -by)
    for d, color in ((logo_marca.AZUL, AZUL), (logo_marca.AMARILLO, AMARILLO), (logo_marca.ROJO, ROJO),
                     (logo_marca.BLANCO, BLANCO), (logo_marca.TEXTO, color_texto)):
        c.setFillColor(color)
        c.drawPath(_trazo(c, d), stroke=0, fill=1, fillMode=0)  # 0 = par-impar, como en la web
    c.restoreState()

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

def _fuentes() -> dict[str, str]:
    """Una sola familia tipográfica en todo el PDF: Helvetica (la misma del texto del logo).

    Viene incluida en ReportLab, así que no requiere archivos de fuentes.
    La clave "serif" se conserva por compatibilidad: ahora es Helvetica negrita."""
    return {"serif": "Helvetica-Bold", "sans": "Helvetica", "sans_bold": "Helvetica-Bold"}


def _fecha_larga(fecha: datetime) -> str:
    return f"{DIAS[fecha.weekday()].capitalize()} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def _texto_espaciado(c: canvas.Canvas, x: float, y: float, texto: str, fuente: str,
                     tamano: float, color, espacio: float = 0.8) -> None:
    t = c.beginText(x, y)
    t.setFont(fuente, tamano)
    t.setFillColor(color)
    t.setCharSpace(espacio)
    t.textOut(texto)
    t.setCharSpace(0)  # que el espaciado no afecte a los textos siguientes
    c.drawText(t)


def _dato(c: canvas.Canvas, f: dict, x: float, y: float, etiqueta: str, valor: str, ancho: float) -> None:
    _texto_espaciado(c, x, y, etiqueta.upper(), f["sans"], 6.5, GRIS)
    lineas = simpleSplit(valor, f["sans_bold"], 10, ancho)[:2]
    c.setFont(f["sans_bold"], 10)
    c.setFillColor(NEGRO)
    for i, linea in enumerate(lineas):
        c.drawString(x, y - 4.6 * mm - i * 4.2 * mm, linea)


def crear_pdf_entrada(destino: Path, entrada: dict) -> None:
    """entrada: codigo, numero, total_orden, evento_nombre, evento_fecha, evento_lugar, sector_nombre."""
    f = _fuentes()
    ancho, alto = A6  # 105 x 148 mm
    margen = 8 * mm
    util = ancho - 2 * margen

    c = canvas.Canvas(str(destino), pagesize=A6)
    c.setTitle(f"Entrada {entrada['codigo']}")
    c.setAuthor("EntradasYa")

    # Fondo de la marca
    c.setFillColor(FONDO)
    c.rect(0, 0, ancho, alto, stroke=0, fill=1)

    # Franja superior negra de 105 x 50 mm (reemplaza a la foto del evento)
    franja = 50 * mm
    c.setFillColor(NEGRO)
    c.rect(0, alto - franja, ancho, franja, stroke=0, fill=1)

    # Franja de 3 colores del logo al pie de la zona negra
    tercio = ancho / 3
    for i, color in enumerate((AZUL, AMARILLO, ROJO)):
        c.setFillColor(color)
        c.rect(i * tercio, alto - franja, tercio + 0.5, 1.6 * mm, stroke=0, fill=1)

    alto_logo = 7 * mm
    _logo(c, margen, alto - margen - alto_logo + 1 * mm, alto_logo, BLANCO)
    numero = f"{entrada['numero']} / {entrada['total_orden']}"
    c.setFont(f["sans"], 7)
    c.setFillColor(BLANCO)
    c.drawRightString(ancho - margen, alto - margen - 3 * mm, f"ENTRADA {numero}")

    # Nombre del evento en Helvetica negrita 24 pt (baja a 18 pt si no entra en dos líneas)
    tamano = 24
    lineas = simpleSplit(entrada["evento_nombre"], f["serif"], tamano, util)
    if len(lineas) > 2:
        tamano = 18
        lineas = simpleSplit(entrada["evento_nombre"], f["serif"], tamano, util)[:3]
    c.setFont(f["serif"], tamano)
    c.setFillColor(BLANCO)
    base = alto - franja + margen
    for i, linea in enumerate(reversed(lineas)):
        c.drawString(margen, base + i * tamano * 0.95, linea)

    # Datos del evento
    fecha: datetime = entrada["evento_fecha"]
    y = alto - franja - 9 * mm
    _dato(c, f, margen, y, "Fecha", _fecha_larga(fecha), util * 0.66)
    _dato(c, f, margen + util * 0.70, y, "Hora", fecha.strftime("%H:%M"), util * 0.30)
    y -= 13 * mm
    _dato(c, f, margen, y, "Lugar", entrada["evento_lugar"], util * 0.66)
    _dato(c, f, margen + util * 0.70, y, "Sector", entrada["sector_nombre"], util * 0.30)

    # Línea divisoria
    y_linea = y - 11 * mm
    c.setStrokeColor(BORDE)
    c.setLineWidth(1)
    c.line(margen, y_linea, ancho - margen, y_linea)

    # Código QR (38 x 38 mm, mayor al mínimo de 35 mm)
    lado_qr = 38 * mm
    x_qr = (ancho - lado_qr) / 2
    y_qr = 19 * mm
    c.setFillColor(BLANCO)
    c.roundRect(x_qr - 2 * mm, y_qr - 2 * mm, lado_qr + 4 * mm, lado_qr + 4 * mm, 2 * mm, stroke=0, fill=1)
    c.drawImage(ImageReader(generar_qr_png(entrada["codigo"])), x_qr, y_qr, lado_qr, lado_qr)

    # Código en texto (8 pt) y aviso
    c.setFont(f["sans_bold"], 8)
    c.setFillColor(NEGRO)
    c.drawCentredString(ancho / 2, y_qr - 7 * mm, entrada["codigo"])
    c.setFont(f["sans"], 6.5)
    c.setFillColor(GRIS)
    c.drawCentredString(ancho / 2, margen - 1 * mm, "Válida para un solo ingreso · Presenta este QR en la puerta")

    c.showPage()
    c.save()
