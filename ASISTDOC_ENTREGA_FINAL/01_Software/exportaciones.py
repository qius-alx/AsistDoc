import os
import sqlite3
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from database import get_connection, DB_PATH
from cursos import obtener_curso_por_id
from alumnos import listar_alumnos_curso
from notas import obtener_matriz_notas_curso, listar_evaluaciones_curso
from reportes import analizar_alumnos_en_riesgo, calcular_estadisticas_asistencia_alumno, obtener_estadisticas_generales_curso

EXPORTS_DIR = "exports"

def asegurar_directorio_exports():
    os.makedirs(EXPORTS_DIR, exist_ok=True)

# --- EXPORTACIÓN EXCEL CON OPENPYXL ---

def exportar_acta_notas_excel(curso_id: int, db_path: str = DB_PATH) -> str:
    """
    Genera Acta de Notas en Excel formateada con openpyxl.
    """
    asegurar_directorio_exports()
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    if not curso:
        raise ValueError("Curso no encontrado.")

    df = obtener_matriz_notas_curso(curso_id, db_path=db_path)

    wb = Workbook()
    ws = wb.active
    ws.title = "Acta de Notas"

    # Estilos
    font_titulo = Font(name="Calibri", size=14, bold=True, color="1F497D")
    font_subtitulo = Font(name="Calibri", size=11, italic=True, color="595959")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")

    border_thin = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    fill_aprobado = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    fill_desaprobado = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

    # Encabezado
    ws['A1'] = f"ACTA DE NOTAS — {curso['nombre'].upper()} (SECCIÓN {curso['seccion']})"
    ws['A1'].font = font_titulo
    ws['A2'] = f"Periodo Lectivo: {curso['periodo_nombre']} | Fecha de Generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws['A2'].font = font_subtitulo

    # Cabeceras de Tabla
    row_idx = 4
    for col_idx, col_name in enumerate(df.columns, 1):
        cell = ws.cell(row=row_idx, column=col_idx, value=col_name)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Datos
    for r_idx, row in df.iterrows():
        current_row = row_idx + 1 + r_idx
        for c_idx, col_name in enumerate(df.columns, 1):
            val = row[col_name]
            cell = ws.cell(row=current_row, column=c_idx, value=val)
            cell.border = border_thin

            if col_name in ["Código", "Promedio", "Condición"]:
                cell.alignment = Alignment(horizontal="center")
            elif col_name == "Alumno":
                cell.alignment = Alignment(horizontal="left")
            else:
                cell.alignment = Alignment(horizontal="center")

            # Colorear Condición y Promedio
            if col_name == "Condición":
                if val == "APROBADO":
                    cell.fill = fill_aprobado
                elif val == "DESAPROBADO":
                    cell.fill = fill_desaprobado

    # Congelar Paneles
    ws.freeze_panes = "A5"

    # Auto-ajustar ancho de columnas
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    filename = f"AsistDoc_{curso['nombre'].replace(' ', '_')}_Notas.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    wb.save(filepath)
    return filepath

def exportar_reporte_riesgo_excel(curso_id: int, db_path: str = DB_PATH) -> str:
    """
    Genera Reporte de Alumnos en Riesgo en Excel con motivos detallados.
    """
    asegurar_directorio_exports()
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    riesgo_list = analizar_alumnos_en_riesgo(curso_id, db_path=db_path)

    wb = Workbook()
    ws = wb.active
    ws.title = "Alumnos en Riesgo"

    font_titulo = Font(name="Calibri", size=14, bold=True, color="C00000")
    ws['A1'] = f"REPORTE DE ALUMNOS EN RIESGO ACADÉMICO — {curso['nombre'].upper()}"
    ws['A1'].font = font_titulo

    headers = ["Código", "Alumno", "Promedio", "% Asistencia", "% Faltas", "Nivel Riesgo", "Motivos"]
    ws.append([]) # Fila vacía
    ws.append(headers)

    for cell in ws[3]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")

    for r in riesgo_list:
        ws.append([
            r['codigo'], r['nombre'], r['promedio'], r['pct_asistencia'],
            r['pct_faltas'], r['nivel_riesgo'], r['motivos']
        ])

    filename = f"AsistDoc_{curso['nombre'].replace(' ', '_')}_Riesgo.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)
    wb.save(filepath)
    return filepath

# --- EXPORTACIÓN PDF CON REPORTLAB ---

def exportar_acta_notas_pdf(curso_id: int, db_path: str = DB_PATH) -> str:
    """
    Genera Acta Oficial de Notas imprimible en PDF con ReportLab.
    """
    asegurar_directorio_exports()
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    if not curso:
        raise ValueError("Curso no encontrado.")

    df = obtener_matriz_notas_curso(curso_id, db_path=db_path)

    filename = f"AsistDoc_{curso['nombre'].replace(' ', '_')}_Acta.pdf"
    filepath = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1F497D'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#595959'),
        spaceAfter=12
    )

    elements = []
    elements.append(Paragraph(f"ACTA DE NOTAS — {curso['nombre'].upper()} ({curso['seccion']})", title_style))
    elements.append(Paragraph(f"Periodo: {curso['periodo_nombre']} | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))

    # Preparar Datos de Tabla
    table_data = [list(df.columns)]
    for _, row in df.iterrows():
        table_data.append([str(val) for val in row.values])

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))

    elements.append(t)
    doc.build(elements)
    return filepath
