import sqlite3
import os
import shutil
from datetime import datetime
from database import DB_PATH, get_connection, init_db, registrar_historial

BACKUPS_DIR = "backups"

def asegurar_directorio_backups():
    os.makedirs(BACKUPS_DIR, exist_ok=True)

def crear_backup_base_datos(db_path: str = DB_PATH) -> str:
    asegurar_directorio_backups()
    if not os.path.exists(db_path):
        raise FileNotFoundError("La base de datos original no existe.")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"asistdoc_backup_{timestamp}.db"
    dest_path = os.path.join(BACKUPS_DIR, filename)

    shutil.copy2(db_path, dest_path)
    try:
        registrar_historial("configuracion", 0, "backup", None, filename, "CREAR", db_path)
    except sqlite3.OperationalError:
        pass
    return dest_path

def listar_backups_disponibles() -> list:
    asegurar_directorio_backups()
    archivos = [f for f in os.listdir(BACKUPS_DIR) if f.endswith(".db")]
    archivos.sort(reverse=True)
    return archivos

def restaurar_backup_base_datos(filename: str, db_path: str = DB_PATH):
    backup_path = os.path.join(BACKUPS_DIR, filename)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"El archivo de copia de seguridad {filename} no existe.")

    # Sobrescribir archivo de destino directamente con el backup
    shutil.copy2(backup_path, db_path)
