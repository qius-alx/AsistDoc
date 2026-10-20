import sqlite3
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from database import get_connection, DB_PATH, registrar_historial
from utils import normalize_text

def crear_o_obtener_alumno(codigo: str, nombre: str, db_path: str = DB_PATH) -> Tuple[int, bool]:
    """
    Crea un nuevo alumno o retorna el ID si ya existe.
    Retorna (alumno_id, creado_nuevo).
    """
    codigo_clean = codigo.strip().upper()
    nombre_clean = nombre.strip().title()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM alumnos WHERE codigo = ?", (codigo_clean,))
        row = cursor.fetchone()
        if row:
            return row['id'], False

        cursor.execute("INSERT INTO alumnos (codigo, nombre, activo) VALUES (?, ?, 1)", (codigo_clean, nombre_clean))
        alumno_id = cursor.lastrowid
        conn.commit()
        registrar_historial("alumnos", alumno_id, "codigo", None, codigo_clean, "CREAR", db_path)
        return alumno_id, True

def matricular_alumno(alumno_id: int, curso_id: int, db_path: str = DB_PATH) -> bool:
    """
    Matricula a un alumno en un curso.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, activo FROM matriculas WHERE alumno_id = ? AND curso_id = ?", (alumno_id, curso_id))
        row = cursor.fetchone()
        if row:
            if row['activo'] == 0:
                cursor.execute("UPDATE matriculas SET activo = 1 WHERE id = ?", (row['id'],))
                conn.commit()
                return True
            return False # Ya matriculado activo

        cursor.execute("INSERT INTO matriculas (alumno_id, curso_id, activo) VALUES (?, ?, 1)", (alumno_id, curso_id))
        conn.commit()
        return True

def retirar_alumno_de_curso(alumno_id: int, curso_id: int, db_path: str = DB_PATH):
    """
    Retira un alumno de un curso (desactivación lógica de matrícula). Preserva su historial de notas/asistencias.
    """
    with get_connection(db_path) as conn:
        conn.execute("UPDATE matriculas SET activo = 0 WHERE alumno_id = ? AND curso_id = ?", (alumno_id, curso_id))
        conn.commit()
        registrar_historial("matriculas", alumno_id, "activo", "1", "0", "MODIFICAR", db_path)

def listar_alumnos_curso(curso_id: int, solo_activos: bool = True, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    """
    Obtiene los alumnos matriculados en un curso.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
        SELECT a.id, a.codigo, a.nombre, m.activo as matricula_activa, m.fecha_matricula
        FROM alumnos a
        JOIN matriculas m ON a.id = m.alumno_id
        WHERE m.curso_id = ?
        """
        params = [curso_id]
        if solo_activos:
            query += " AND m.activo = 1 AND a.activo = 1"
        query += " ORDER BY a.nombre"
        cursor.execute(query, params)
        return cursor.fetchall()

def buscar_alumnos_en_curso(curso_id: int, termino: str, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    """
    Busca alumnos matriculados en un curso aplicando normalización Unicode (sin tildes, minúsculas, coincidencia parcial).
    """
    alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)
    if not termino.strip():
        return alumnos

    term_norm = normalize_text(termino)
    coincidencias = []
    for a in alumnos:
        codigo_norm = normalize_text(a['codigo'])
        nombre_norm = normalize_text(a['nombre'])
        if term_norm in codigo_norm or term_norm in nombre_norm:
            coincidencias.append(a)
    return coincidencias

def importar_alumnos_df(df: pd.DataFrame, curso_id: int, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Valida e importa alumnos desde un DataFrame (CSV/Excel).
    Requiere columnas 'codigo' y 'nombre'.
    """
    resumen = {
        "total": len(df),
        "exitosos": 0,
        "duplicados_curso": 0,
        "invalidos": 0,
        "errores": []
    }

    cols = [c.lower().strip() for c in df.columns]
    df.columns = cols

    if 'codigo' not in df.columns or 'nombre' not in df.columns:
        resumen["errores"].append("El archivo debe contener las columnas 'codigo' y 'nombre'.")
        return resumen

    for idx, row in df.iterrows():
        cod = str(row['codigo']).strip() if pd.notna(row['codigo']) else ""
        nom = str(row['nombre']).strip() if pd.notna(row['nombre']) else ""

        if not cod or not nom or cod.lower() == 'nan' or nom.lower() == 'nan':
            resumen["invalidos"] += 1
            resumen["errores"].append(f"Fila {idx+1}: Código o nombre vacío/inválido.")
            continue

        try:
            alumno_id, _ = crear_o_obtener_alumno(cod, nom, db_path)
            matriculado = matricular_alumno(alumno_id, curso_id, db_path)
            if matriculado:
                resumen["exitosos"] += 1
            else:
                resumen["duplicados_curso"] += 1
        except Exception as e:
            resumen["invalidos"] += 1
            resumen["errores"].append(f"Fila {idx+1} ({cod}): {str(e)}")

    return resumen
