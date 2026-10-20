import pytest
import os
import tempfile
from database import init_db
from cursos import crear_periodo, crear_curso
from alumnos import crear_o_obtener_alumno, matricular_alumno
from notas import (
    crear_evaluacion, registrar_o_actualizar_nota,
    calcular_promedio_alumno, calcular_nota_necesaria
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_notes_validations_and_exact_math(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    # Course with rounding rule desde 0.5
    c_id = crear_curso(p_id, "Redes II", "A", nota_minima=11.0, escala_max=20.0, redondeo_desde=0.5, db_path=temp_db)

    a_id, _ = crear_o_obtener_alumno("2026001", "Carlos Mamani", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    # 1. Validation checks
    e1 = crear_evaluacion(c_id, "P1", 20.0, db_path=temp_db)
    e2 = crear_evaluacion(c_id, "Parcial", 30.0, db_path=temp_db)
    e3 = crear_evaluacion(c_id, "Final", 50.0, db_path=temp_db)

    # Rejections: >20.0, <0.0, letters
    with pytest.raises(ValueError):
        registrar_o_actualizar_nota(a_id, e1, valor=20.1, estado='registrada', db_path=temp_db)
    with pytest.raises(ValueError):
        registrar_o_actualizar_nota(a_id, e1, valor=-1.0, estado='registrada', db_path=temp_db)

    # Valid values: 10 in P1 (20%), 14 in Parcial (30%), 16 in Final (50%)
    # Expected exact weighted sum: 10*0.2 + 14*0.3 + 16*0.5 = 2.0 + 4.2 + 8.0 = 14.2
    registrar_o_actualizar_nota(a_id, e1, valor=10.0, estado='registrada', db_path=temp_db)
    registrar_o_actualizar_nota(a_id, e2, valor=14.0, estado='registrada', db_path=temp_db)
    registrar_o_actualizar_nota(a_id, e3, valor=16.0, estado='registrada', db_path=temp_db)

    res_prom = calcular_promedio_alumno(a_id, c_id, db_path=temp_db)
    assert res_prom['promedio_raw'] == 14.2
    assert res_prom['promedio_final'] == 14.0 # 14.2 redondea abajo

def test_rounding_thresholds(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Física", "A", nota_minima=11.0, escala_max=20.0, redondeo_desde=0.5, db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026002", "Ana Ruiz", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "E1", 100.0, db_path=temp_db)

    # 10.49 -> 10.0
    registrar_o_actualizar_nota(a_id, e1, valor=10.49, estado='registrada', db_path=temp_db)
    p1 = calcular_promedio_alumno(a_id, c_id, db_path=temp_db)
    assert p1['promedio_final'] == 10.0

    # 10.50 -> 11.0
    registrar_o_actualizar_nota(a_id, e1, valor=10.50, estado='registrada', db_path=temp_db)
    p2 = calcular_promedio_alumno(a_id, c_id, db_path=temp_db)
    assert p2['promedio_final'] == 11.0

def test_cuanto_necesita_cases(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Química", "A", nota_minima=11.0, escala_max=20.0, db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026003", "Pedro Soto", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "Parcial", 50.0, db_path=temp_db)
    e2 = crear_evaluacion(c_id, "Final", 50.0, db_path=temp_db)

    # Case 1: Alumno has 16 in Parcial (8.0 accumulated >= 11.0? No, needs 3.0 in 50% -> 6.0)
    registrar_o_actualizar_nota(a_id, e1, valor=16.0, estado='registrada', db_path=temp_db)
    cn1 = calcular_nota_necesaria(a_id, c_id, e2, db_path=temp_db)
    assert cn1['alcanzable'] is True
    assert cn1['nota_necesaria'] == 6.0

    # Case 2: Alumno has 0.0 in Parcial (0 accumulated -> needs 11.0 in 50% -> 22.0 > 20 -> Not reachable)
    registrar_o_actualizar_nota(a_id, e1, valor=0.0, estado='registrada', db_path=temp_db)
    cn2 = calcular_nota_necesaria(a_id, c_id, e2, db_path=temp_db)
    assert cn2['alcanzable'] is False

    # Case 3: Already approved (22.0 in Parcial? Max 20 -> 20 in Parcial = 10.0 accumulated + Parcial 50%... wait, if 22 in e1 -> 11.0 accumulated = 11.0 -> Goal reached)
    registrar_o_actualizar_nota(a_id, e1, valor=20.0, estado='registrada', db_path=temp_db)
    # If student has 20 in Parcial (50%) = 10.0 accumulated. Still needs 1.0 -> 2.0 in Final
    cn3 = calcular_nota_necesaria(a_id, c_id, e2, db_path=temp_db)
    assert cn3['alcanzable'] is True
    assert cn3['nota_necesaria'] == 2.0
