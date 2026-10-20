import pytest
from qr_utils import generar_codigo_qr_bytes, generar_carnet_alumno, decodificar_qr_texto

def test_qr_utils():
    codigo = "2026001"
    nombre = "Carlos Mamani"

    # 1. Generar QR Bytes
    qr_bytes = generar_codigo_qr_bytes(codigo)
    assert len(qr_bytes) > 0

    # 2. Generar Carnet Bytes
    carnet_bytes = generar_carnet_alumno(codigo, nombre)
    assert len(carnet_bytes) > 0

    # 3. Decodificar QR
    cod_valid = decodificar_qr_texto("ASISTDOC|ALUMNO|2026001")
    assert cod_valid == "2026001"

    cod_invalid = decodificar_qr_texto("OTRO_FORMATO|12345")
    assert cod_invalid is None
