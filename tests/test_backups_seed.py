import pytest
import os
import tempfile
from database import init_db
from backups import crear_backup_base_datos, listar_backups_disponibles, restaurar_backup_base_datos
from seed import poblar_datos_demostracion

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_backups_y_seed(temp_db):
    # Test Seed
    poblar_datos_demostracion(temp_db)

    # Test Backup
    backup_path = crear_backup_base_datos(temp_db)
    assert os.path.exists(backup_path)

    # List Backups
    backups = listar_backups_disponibles()
    assert len(backups) > 0

    # Test Restore
    filename = os.path.basename(backup_path)
    restaurar_backup_base_datos(filename, db_path=temp_db)
    assert os.path.exists(temp_db)
