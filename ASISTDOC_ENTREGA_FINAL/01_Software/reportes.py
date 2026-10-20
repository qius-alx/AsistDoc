import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from database import get_connection, DB_PATH
from config import RIESGO_NINGUNO, RIESGO_ATENCION, RIESGO_ALTO
from cursos import obtener_curso_por_id
from alumnos import listar_alumnos_curso
from notas import calcular_promedio_alumno, listar_evaluaciones_curso

def calcular_estadisticas_asistencia_alumno(alumno_id: int, curso_id: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Calcula porcentaje y conteo de asistencia de un alumno en un curso.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.estado, COUNT(*) as cantidad
        FROM asistencias a
        JOIN sesiones_asistencia s ON a.sesion_id = s.id
        WHERE a.alumno_id = ? AND s.curso_id = ?
        GROUP BY a.estado
        """, (alumno_id, curso_id))
        rows = cursor.fetchall()
        counts = {r['estado']: r['cantidad'] for r in rows}

        presentes = counts.get('presente', 0)
        tardanzas = counts.get('tardanza', 0)
        faltas = counts.get('falta', 0)
        justificadas = counts.get('justificada', 0)

        total_sesiones = presentes + tardanzas + faltas + justificadas
        if total_sesiones == 0:
            return {
                "porcentaje_asistencia": 100.0,
                "porcentaje_faltas": 0.0,
                "presentes": 0, "tardanzas": 0, "faltas": 0, "justificadas": 0,
                "total_sesiones": 0
            }

        # Asistencia efectiva = (presentes + 0.5 * tardanzas + justificadas) / total
        pct_asistencia = round(((presentes + 0.5 * tardanzas + justificadas) / total_sesiones) * 100, 1)
        pct_faltas = round((faltas / total_sesiones) * 100, 1)

        return {
            "porcentaje_asistencia": pct_asistencia,
            "porcentaje_faltas": pct_faltas,
            "presentes": presentes,
            "tardanzas": tardanzas,
            "faltas": faltas,
            "justificadas": justificadas,
            "total_sesiones": total_sesiones
        }

def analizar_alumnos_en_riesgo(curso_id: int, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """
    Motor de Reglas de Clasificación de Alumnos en Riesgo:

    Regla 1: Rendimiento
    - promedio < nota_minima (Riesgo Rendimiento)

    Regla 2: Asistencia
    - porcentaje_faltas >= limite_faltas_pct (Riesgo Asistencia)

    Niveles:
    - ALTO RIESGO: Faltas excesivas Y Promedio desaprobado (o desaprobado crítico < 08.0)
    - ATENCIÓN: Cumple 1 de las 2 condiciones o promedio bordeando nota mínima.
    - NORMAL: Cumple ambos requisitos.
    """
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    if not curso:
        raise ValueError("Curso no encontrado.")

    nota_minima = curso['nota_minima']
    limite_faltas_pct = curso['limite_faltas_pct']
    alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)

    analisis = []
    for a in alumnos:
        res_prom = calcular_promedio_alumno(a['id'], curso_id, db_path=db_path)
        res_asist = calcular_estadisticas_asistencia_alumno(a['id'], curso_id, db_path=db_path)

        prom = res_prom['promedio_final']
        pct_faltas = res_asist['porcentaje_faltas']

        motivos = []
        riesgo_notas = prom < nota_minima
        riesgo_asistencia = pct_faltas >= limite_faltas_pct

        if riesgo_notas:
            motivos.append(f"Promedio desaprobado ({prom:.1f} < {nota_minima:.1f})")
        if riesgo_asistencia:
            motivos.append(f"Exceso de faltas ({pct_faltas:.1f}% >= {limite_faltas_pct:.1f}%)")

        if riesgo_notas and riesgo_asistencia:
            nivel = RIESGO_ALTO
        elif riesgo_notas or riesgo_asistencia or (prom < nota_minima + 1.5):
            nivel = RIESGO_ATENCION
            if not motivos:
                motivos.append(f"Promedio en rango de riesgo/atención ({prom:.1f})")
        else:
            nivel = RIESGO_NINGUNO

        analisis.append({
            "alumno_id": a['id'],
            "codigo": a['codigo'],
            "nombre": a['nombre'],
            "promedio": prom,
            "pct_asistencia": res_asist['porcentaje_asistencia'],
            "pct_faltas": pct_faltas,
            "nivel_riesgo": nivel,
            "motivos": "; ".join(motivos) if motivos else "Ninguno"
        })

    return analisis

def obtener_estadisticas_generales_curso(curso_id: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Retorna métricas globales del curso para dashboards y reportes.
    """
    alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)
    if not alumnos:
        return {
            "total_alumnos": 0, "aprobados": 0, "desaprobados": 0,
            "promedio_general": 0.0, "asistencia_promedio": 0.0,
            "alumnos_en_riesgo": 0
        }

    promedios = []
    asistencias = []
    aprobados = 0
    desaprobados = 0

    riesgo_list = analizar_alumnos_en_riesgo(curso_id, db_path=db_path)
    cant_riesgo = sum(1 for r in riesgo_list if r['nivel_riesgo'] in [RIESGO_ALTO, RIESGO_ATENCION])

    for a in alumnos:
        res_prom = calcular_promedio_alumno(a['id'], curso_id, db_path=db_path)
        res_asist = calcular_estadisticas_asistencia_alumno(a['id'], curso_id, db_path=db_path)

        promedios.append(res_prom['promedio_final'])
        asistencias.append(res_asist['porcentaje_asistencia'])

        if res_prom['condicion'] == 'APROBADO':
            aprobados += 1
        else:
            desaprobados += 1

    prom_gen = sum(promedios) / len(promedios) if promedios else 0.0
    asist_gen = sum(asistencias) / len(asistencias) if asistencias else 0.0

    return {
        "total_alumnos": len(alumnos),
        "aprobados": aprobados,
        "desaprobados": desaprobados,
        "pct_aprobados": round((aprobados / len(alumnos)) * 100, 1),
        "promedio_general": round(prom_gen, 2),
        "asistencia_promedio": round(asist_gen, 1),
        "alumnos_en_riesgo": cant_riesgo
    }

# --- GRÁFICOS PLOTLY ---

def generar_grafico_distribucion_notas(curso_id: int, db_path: str = DB_PATH):
    """
    Genera histograma de distribución de promedios con Plotly.
    """
    alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)
    promedios = [calcular_promedio_alumno(a['id'], curso_id, db_path=db_path)['promedio_final'] for a in alumnos]

    df = pd.DataFrame({"Promedio": promedios})
    fig = px.histogram(
        df, x="Promedio", nbins=10,
        title="Distribución de Promedios del Curso",
        labels={"Promedio": "Promedio Final"},
        color_discrete_sequence=['#1f77b4']
    )
    fig.update_layout(xaxis_range=[0, 20], yaxis_title="Cantidad de Alumnos")
    return fig

def generar_grafico_resumen_asistencia(curso_id: int, db_path: str = DB_PATH):
    """
    Genera gráfico de dona con el resumen total de asistencias del curso.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.estado, COUNT(*) as total
        FROM asistencias a
        JOIN sesiones_asistencia s ON a.sesion_id = s.id
        WHERE s.curso_id = ?
        GROUP BY a.estado
        """, (curso_id,))
        rows = cursor.fetchall()

    data = {r['estado']: r['total'] for r in rows}
    labels = list(data.keys())
    values = list(data.values())

    fig = px.pie(
        names=labels, values=values, hole=0.4,
        title="Resumen General de Asistencia",
        color=labels,
        color_discrete_map={
            "presente": "#2ca02c",
            "tardanza": "#ff7f0e",
            "falta": "#d62728",
            "justificada": "#17becf"
        }
    )
    return fig
