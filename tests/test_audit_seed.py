import pytest
import os
import tempfile
import sqlite3
from database import init_db, get_connection
from seed import poblar_datos_demostracion

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_seed_execution_and_reexecution(temp_db):
    # First execution
    poblar_datos_demostracion(temp_db)

    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alumnos;")
    cant_alumnos = cursor.fetchone()[0]
    assert cant_alumnos == 30

    cursor.execute("SELECT COUNT(*) FROM cursos;")
    cant_cursos = cursor.fetchone()[0]
    assert cant_cursos == 2

    conn.close()

    # Second execution should complete cleanly without throwing exceptions
    poblar_datos_demostracion(temp_db)

    conn = get_connection(temp_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    assert cursor.fetchone()[0] == "ok"
    cursor.execute("PRAGMA foreign_key_check;")
    assert len(cursor.fetchall()) == 0
    conn.close()
