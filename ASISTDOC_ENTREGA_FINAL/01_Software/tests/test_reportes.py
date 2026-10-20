import pytest
import os
import tempfile
from database import init_db
from cursos import crear_periodo, crear_curso
from alumnos import crear_o_obtener_alumno, matricular_alumno
from notas import crear_evaluacion, registrar_o_actualizar_nota
from asistencia import obtener_o_crear_sesion, registrar_asistencia_individual
from reportes import (
    analizar_alumnos_en_riesgo,
    obtener_estadisticas_generales_curso,
    calcular_estadisticas_asistencia_alumno
)
from config import RIESGO_ALTO, RIESGO_ATENCION, RIESGO_NINGUNO

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_motor_riesgo(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", nota_minima=11.0, limite_faltas_pct=30.0, db_path=temp_db)

    a1_id, _ = crear_o_obtener_alumno("2026001", "Carlos Riesgo Alto", db_path=temp_db)
    a2_id, _ = crear_o_obtener_alumno("2026002", "Ana Normal", db_path=temp_db)
    matricular_alumno(a1_id, c_id, db_path=temp_db)
    matricular_alumno(a2_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "Examen", 100.0, db_path=temp_db)
    registrar_o_actualizar_nota(a1_id, e1, valor=08.0, estado='registrada', db_path=temp_db)
    registrar_o_actualizar_nota(a2_id, e1, valor=16.0, estado='registrada', db_path=temp_db)

    # Crear 4 sesiones de asistencia
    for i in range(1, 5):
        s_id, _ = obtener_o_crear_sesion(c_id, fecha=f"2026-10-0{i}", db_path=temp_db)
        # a1 falta a 3 de 4 clases (75% faltas > 30% limite)
        if i <= 3:
            registrar_asistencia_individual(s_id, a1_id, estado='falta', db_path=temp_db)
        else:
            registrar_asistencia_individual(s_id, a1_id, estado='presente', db_path=temp_db)

        # a2 asistió a todas
        registrar_asistencia_individual(s_id, a2_id, estado='presente', db_path=temp_db)

    riesgo_list = analizar_alumnos_en_riesgo(c_id, db_path=temp_db)
    assert len(riesgo_list) == 2

    a1_res = next(r for r in riesgo_list if r['alumno_id'] == a1_id)
    a2_res = next(r for r in riesgo_list if r['alumno_id'] == a2_id)

    assert a1_res['nivel_riesgo'] == RIESGO_ALTO
    assert a2_res['nivel_riesgo'] == RIESGO_NINGUNO

def test_estadisticas_generales(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Base de Datos", "B", db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026005", "Pedro Soto", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    stats = obtener_estadisticas_generales_curso(c_id, db_path=temp_db)
    assert stats['total_alumnos'] == 1
