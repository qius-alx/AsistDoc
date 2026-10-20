import os
import qrcode
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional

EXPORTS_DIR = "exports"

def generar_codigo_qr_bytes(codigo_alumno: str) -> bytes:
    """
    Genera la imagen QR en bytes para el formato seguro: ASISTDOC|ALUMNO|CODIGO
    """
    contenido = f"ASISTDOC|ALUMNO|{codigo_alumno.strip().upper()}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generar_carnet_alumno(codigo_alumno: str, nombre_alumno: str) -> bytes:
    """
    Genera un carnet impreso virtual (PNG) con nombre, código y QR del estudiante.
    """
    # Crear lienzo de carnet (400 x 250 px)
    width, height = 400, 250
    carnet = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(carnet)

    # Encabezado institucional
    draw.rectangle([(0, 0), (width, 45)], fill=(31, 73, 125))
    draw.text((15, 12), "ASISTDOC — Carnet de Estudiante", fill=(255, 255, 255))

    # Generar QR e insertarlo
    qr_bytes = generar_codigo_qr_bytes(codigo_alumno)
    qr_img = Image.open(BytesIO(qr_bytes)).resize((140, 140))
    carnet.paste(qr_img, (15, 60))

    # Texto de datos de alumno
    draw.text((170, 75), f"Código:", fill=(100, 100, 100))
    draw.text((170, 95), codigo_alumno.upper(), fill=(0, 0, 0))

    draw.text((170, 130), f"Estudiante:", fill=(100, 100, 100))
    draw.text((170, 150), nombre_alumno[:25], fill=(0, 0, 0))

    # Borde exterior
    draw.rectangle([(0, 0), (width-1, height-1)], outline=(200, 200, 200), width=2)

    buf = BytesIO()
    carnet.save(buf, format="PNG")
    return buf.getvalue()

def decodificar_qr_texto(contenido_qr: str) -> Optional[str]:
    """
    Decodifica el string QR si cumple el formato seguro ASISTDOC|ALUMNO|CODIGO.
    Retorna el código del alumno o None si no es válido.
    """
    parts = contenido_qr.strip().split("|")
    if len(parts) == 3 and parts[0] == "ASISTDOC" and parts[1] == "ALUMNO":
        return parts[2]
    return None
