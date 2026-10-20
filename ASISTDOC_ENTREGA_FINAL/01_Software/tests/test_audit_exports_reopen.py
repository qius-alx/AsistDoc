import pytest
import os
import tempfile
import openpyxl
from database import init_db
from cursos import crear_periodo, crear_curso
from alumnos import crear_o_obtener_alumno, matricular_alumno
from notas import crear_evaluacion, registrar_o_actualizar_nota
from exportaciones import (
    exportar_acta_notas_excel, exportar_reporte_riesgo_excel, exportar_acta_notas_pdf
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_reports_excel_reopening_and_pdf(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026001", "Carlos Mamani", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "P1", 100.0, db_path=temp_db)
    registrar_o_actualizar_nota(a_id, e1, valor=15.0, estado='registrada', db_path=temp_db)

    # 1. Generate Excel Acta
    excel_acta_path = exportar_acta_notas_excel(c_id, db_path=temp_db)
    assert os.path.exists(excel_acta_path)

    # Re-open with openpyxl to verify valid format and structure
    wb_acta = openpyxl.load_workbook(excel_acta_path)
    sheet_acta = wb_acta.active
    assert sheet_acta.title == "Acta de Notas"
    assert "ACTA DE NOTAS" in sheet_acta['A1'].value

    # 2. Generate Excel Riesgo
    excel_riesgo_path = exportar_reporte_riesgo_excel(c_id, db_path=temp_db)
    assert os.path.exists(excel_riesgo_path)
    wb_riesgo = openpyxl.load_workbook(excel_riesgo_path)
    assert wb_riesgo.active.title == "Alumnos en Riesgo"

    # 3. Generate PDF
    pdf_path = exportar_acta_notas_pdf(c_id, db_path=temp_db)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
