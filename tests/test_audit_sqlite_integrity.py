import pytest
import os
import sqlite3
import tempfile
from database import init_db, get_connection

@pytest.fixture
def clean_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_sqlite_pragma_checks(clean_db):
    conn = get_connection(clean_db)
    cursor = conn.cursor()

    # 1. PRAGMA integrity_check
    cursor.execute("PRAGMA integrity_check;")
    res_integrity = cursor.fetchone()[0]
    assert res_integrity == "ok"

    # 2. PRAGMA foreign_key_check
    cursor.execute("PRAGMA foreign_key_check;")
    res_fk = cursor.fetchall()
    assert len(res_fk) == 0

    conn.close()

def test_deliberate_constraint_violations(clean_db):
    conn = get_connection(clean_db)
    cursor = conn.cursor()

    # Insert base periodo and curso
    cursor.execute("INSERT INTO periodos (nombre, fecha_inicio, fecha_fin) VALUES ('2026-I', '2026-03-01', '2026-07-31')")
    p_id = cursor.lastrowid
    cursor.execute("INSERT INTO cursos (periodo_id, nombre, seccion) VALUES (?, 'Física', 'A')", (p_id,))
    c_id = cursor.lastrowid
    cursor.execute("INSERT INTO alumnos (codigo, nombre) VALUES ('COD001', 'Juan Perez')")
    a_id = cursor.lastrowid

    # Duplicate alumno codigo
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO alumnos (codigo, nombre) VALUES ('COD001', 'Otro Juan')")

    # Duplicate matricula
    cursor.execute("INSERT INTO matriculas (alumno_id, curso_id) VALUES (?, ?)", (a_id, c_id))
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO matriculas (alumno_id, curso_id) VALUES (?, ?)", (a_id, c_id))

    # Duplicate asistencia in same session
    cursor.execute("INSERT INTO sesiones_asistencia (curso_id, fecha, hora_inicio) VALUES (?, '2026-10-20', '08:00')", (c_id,))
    s_id = cursor.lastrowid
    cursor.execute("INSERT INTO asistencias (sesion_id, alumno_id, estado) VALUES (?, ?, 'presente')", (s_id, a_id))
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO asistencias (sesion_id, alumno_id, estado) VALUES (?, ?, 'tardanza')", (s_id, a_id))

    # Duplicate nota for same evaluation
    cursor.execute("INSERT INTO evaluaciones (curso_id, nombre, peso) VALUES (?, 'Examen 1', 50)", (c_id,))
    e_id = cursor.lastrowid
    cursor.execute("INSERT INTO notas (alumno_id, evaluacion_id, valor, estado) VALUES (?, ?, 15.0, 'registrada')", (a_id, e_id))
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO notas (alumno_id, evaluacion_id, valor, estado) VALUES (?, ?, 18.0, 'registrada')", (a_id, e_id))

    # Invalid CHECK constraint for nota valor > 20
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO notas (alumno_id, evaluacion_id, valor, estado) VALUES (?, ?, 25.0, 'registrada')", (a_id, 999))

    conn.close()
