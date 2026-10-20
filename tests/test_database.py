import pytest
import os
import sqlite3
import tempfile
from database import init_db, get_connection, registrar_historial, obtener_historial_reciente

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_init_db(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    conn.close()

    expected_tables = [
        'periodos', 'cursos', 'horarios', 'alumnos', 'matriculas',
        'sesiones_asistencia', 'asistencias', 'evaluaciones', 'notas',
        'historial', 'configuracion'
    ]
    for table in expected_tables:
        assert table in tables

def test_foreign_keys_and_unique(temp_db):
    conn = get_connection(temp_db)
    cursor = conn.cursor()

    # Insert Periodo
    cursor.execute("INSERT INTO periodos (nombre, fecha_inicio, fecha_fin) VALUES ('2026-I', '2026-03-01', '2026-07-31')")
    periodo_id = cursor.lastrowid

    # Duplicate Periodo Name -> Should raise IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO periodos (nombre, fecha_inicio, fecha_fin) VALUES ('2026-I', '2026-03-01', '2026-07-31')")

    # Foreign key test for Cursos -> Invalid Periodo ID should fail
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO cursos (periodo_id, nombre, seccion) VALUES (999, 'Matemática', 'A')")

    # Valid Curso
    cursor.execute("INSERT INTO cursos (periodo_id, nombre, seccion) VALUES (?, 'Matemática', 'A')", (periodo_id,))
    curso_id = cursor.lastrowid

    # Unique constraint (periodo_id, nombre, seccion)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO cursos (periodo_id, nombre, seccion) VALUES (?, 'Matemática', 'A')", (periodo_id,))

    conn.close()

def test_historial(temp_db):
    registrar_historial("notas", 10, "valor", "12.0", "15.0", "MODIFICAR", temp_db)
    hist = obtener_historial_reciente(10, temp_db)
    assert len(hist) == 1
    assert hist[0]['tabla'] == 'notas'
    assert hist[0]['valor_anterior'] == '12.0'
    assert hist[0]['valor_nuevo'] == '15.0'
    assert hist[0]['accion'] == 'MODIFICAR'
