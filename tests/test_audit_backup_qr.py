import pytest
import os
import tempfile
import sqlite3
from database import init_db, get_connection
from backups import crear_backup_base_datos, restaurar_backup_base_datos
from qr_utils import generar_codigo_qr_bytes, decodificar_qr_texto

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_backup_restore_and_qr_integrity(temp_db):
    conn = get_connection(temp_db)
    conn.execute("INSERT INTO periodos (nombre, fecha_inicio, fecha_fin) VALUES ('2026-I', '2026-03-01', '2026-07-31')")
    conn.commit()
    conn.close()

    # Create backup
    backup_path = crear_backup_base_datos(temp_db)
    assert os.path.exists(backup_path)

    # Restore in temporary target DB
    fd_target, path_target = tempfile.mkstemp(suffix=".db")
    os.close(fd_target)
    init_db(path_target) # Initialize schema

    restaurar_backup_base_datos(os.path.basename(backup_path), db_path=path_target)

    # Check integrity of restored DB
    conn_t = get_connection(path_target)
    cursor = conn_t.cursor()
    cursor.execute("PRAGMA integrity_check;")
    assert cursor.fetchone()[0] == "ok"

    cursor.execute("SELECT COUNT(*) FROM periodos;")
    assert cursor.fetchone()[0] == 1
    conn_t.close()

    if os.path.exists(path_target):
        os.remove(path_target)

    # QR Decodification Test
    qr_b = generar_codigo_qr_bytes("2026001")
    assert len(qr_b) > 0
    assert decodificar_qr_texto("ASISTDOC|ALUMNO|2026001") == "2026001"
    assert decodificar_qr_texto("INVALID_FORMAT") is None
