import pytest
import os
import tempfile
import sqlite3
from database import init_db, get_connection
from cursos import crear_periodo, crear_curso
from alumnos import crear_o_obtener_alumno, matricular_alumno
from notas import (
    crear_evaluacion,
    listar_evaluaciones_curso,
    verificar_suma_pesos,
    registrar_o_actualizar_nota,
    deshacer_ultimo_ingreso_nota,
    calcular_promedio_alumno,
    calcular_nota_necesaria,
    obtener_matriz_notas_curso
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_evaluaciones_y_pesos(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)

    e1 = crear_evaluacion(c_id, "Práctica 1", 30.0, db_path=temp_db)
    e2 = crear_evaluacion(c_id, "Examen Parcial", 30.0, db_path=temp_db)
    e3 = crear_evaluacion(c_id, "Examen Final", 40.0, db_path=temp_db)

    suma, es_100 = verificar_suma_pesos(c_id, db_path=temp_db)
    assert suma == 100.0
    assert es_100 is True

def test_registro_notas_validaciones_y_np(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", nota_minima=11.0, escala_max=20.0, db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026001", "Carlos Mamani", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "P1", 50.0, db_path=temp_db)
    e2 = crear_evaluacion(c_id, "P2", 50.0, db_path=temp_db)

    # Validar rechazo de notas fuera de rango (> 20)
    with pytest.raises(ValueError, match="La nota debe estar entre 0.0 y 20.0"):
        registrar_o_actualizar_nota(a_id, e1, valor=24.0, estado='registrada', db_path=temp_db)

    # Validar rechazo de números negativos
    with pytest.raises(ValueError):
        registrar_o_actualizar_nota(a_id, e1, valor=-2.0, estado='registrada', db_path=temp_db)

    # Registrar NP (debe guardarse con valor NULL y contar como 0 en promedio)
    registrar_o_actualizar_nota(a_id, e1, valor=None, estado='NP', db_path=temp_db)
    # Registrar nota 12
    registrar_o_actualizar_nota(a_id, e2, valor=12.0, estado='registrada', db_path=temp_db)

    # Calcular promedio: (0.0 * 0.5) + (12.0 * 0.5) = 6.0
    prom = calcular_promedio_alumno(a_id, c_id, db_path=temp_db)
    assert prom['promedio_final'] == 6.0
    assert prom['condicion'] == 'DESAPROBADO'

def test_deshacer_ultimo_ingreso(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Base de Datos", "B", db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026002", "Ana Ruiz", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)
    e1 = crear_evaluacion(c_id, "Parcial", 100.0, db_path=temp_db)

    # Registrar nota inicial 10
    registrar_o_actualizar_nota(a_id, e1, valor=10.0, estado='registrada', db_path=temp_db)
    # Cambiar nota a 16
    registrar_o_actualizar_nota(a_id, e1, valor=16.0, estado='registrada', db_path=temp_db)

    # Deshacer debe revertir la nota a 10
    ok = deshacer_ultimo_ingreso_nota(c_id, db_path=temp_db)
    assert ok is True

    prom = calcular_promedio_alumno(a_id, c_id, db_path=temp_db)
    assert prom['promedio_final'] == 10.0

def test_cuanto_necesita(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Sistemas", "A", nota_minima=11.0, escala_max=20.0, db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026003", "Pedro Soto", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    e1 = crear_evaluacion(c_id, "Práctica 1", 60.0, db_path=temp_db)
    e2 = crear_evaluacion(c_id, "Examen Final", 40.0, db_path=temp_db)

    # Alumno saca 8.0 en P1 (8 * 0.6 = 4.8 acumulado)
    registrar_o_actualizar_nota(a_id, e1, valor=8.0, estado='registrada', db_path=temp_db)

    # Para alcanzar 11.0 necesita 11.0 - 4.8 = 6.2 en el 40% restante -> 6.2 / 0.4 = 15.5
    res = calcular_nota_necesaria(a_id, c_id, e2, db_path=temp_db)
    assert res['alcanzable'] is True
    assert res['nota_necesaria'] == 15.5

def test_matriz_notas_df(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)
    a_id, _ = crear_o_obtener_alumno("2026001", "Carlos Mamani", db_path=temp_db)
    matricular_alumno(a_id, c_id, db_path=temp_db)

    crear_evaluacion(c_id, "P1", 100.0, db_path=temp_db)

    df = obtener_matriz_notas_curso(c_id, db_path=temp_db)
    assert "Código" in df.columns
    assert "P1" in df.columns
    assert "Promedio" in df.columns
