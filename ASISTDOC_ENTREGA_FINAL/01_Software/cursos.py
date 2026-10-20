import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from database import get_connection, DB_PATH, registrar_historial
from config import DEFAULT_NOTA_MINIMA, DEFAULT_ESCALA_MAX, DEFAULT_LIMITE_FALTAS_PCT, DEFAULT_REDONDEO_DESDE, DEFAULT_MINUTOS_TOLERANCIA

# --- PERIODOS ---

def crear_o_obtener_periodo(nombre: str, fecha_inicio: str, fecha_fin: str, db_path: str = DB_PATH) -> Tuple[int, bool]:
    """
    Crea un nuevo periodo o retorna el ID si ya existe.
    Retorna (periodo_id, creado_nuevo).
    """
    nom_clean = nombre.strip()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM periodos WHERE nombre = ?", (nom_clean,))
        row = cursor.fetchone()
        if row:
            return row['id'], False

        cursor.execute("""
        INSERT INTO periodos (nombre, fecha_inicio, fecha_fin, activo)
        VALUES (?, ?, ?, 1)
        """, (nom_clean, fecha_inicio, fecha_fin))
        p_id = cursor.lastrowid
        conn.commit()
        registrar_historial("periodos", p_id, "nombre", None, nom_clean, "CREAR", db_path)
        return p_id, True

def crear_periodo(nombre: str, fecha_inicio: str, fecha_fin: str, db_path: str = DB_PATH) -> int:
    p_id, _ = crear_o_obtener_periodo(nombre, fecha_inicio, fecha_fin, db_path)
    return p_id

def listar_periodos(solo_activos: bool = False, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if solo_activos:
            cursor.execute("SELECT * FROM periodos WHERE activo = 1 ORDER BY fecha_inicio DESC")
        else:
            cursor.execute("SELECT * FROM periodos ORDER BY fecha_inicio DESC")
        return cursor.fetchall()

def cambiar_estado_periodo(periodo_id: int, activo: bool, db_path: str = DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("UPDATE periodos SET activo = ? WHERE id = ?", (1 if activo else 0, periodo_id))
        conn.commit()

# --- CURSOS ---

def crear_o_obtener_curso(
    periodo_id: int,
    nombre: str,
    seccion: str,
    nota_minima: float = DEFAULT_NOTA_MINIMA,
    escala_max: float = DEFAULT_ESCALA_MAX,
    limite_faltas_pct: float = DEFAULT_LIMITE_FALTAS_PCT,
    redondeo_desde: float = DEFAULT_REDONDEO_DESDE,
    db_path: str = DB_PATH
) -> Tuple[int, bool]:
    nom_clean = nombre.strip()
    sec_clean = seccion.strip()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cursos WHERE periodo_id = ? AND nombre = ? AND seccion = ?", (periodo_id, nom_clean, sec_clean))
        row = cursor.fetchone()
        if row:
            return row['id'], False

        cursor.execute("""
        INSERT INTO cursos (periodo_id, nombre, seccion, nota_minima, escala_max, limite_faltas_pct, redondeo_desde, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (periodo_id, nom_clean, sec_clean, nota_minima, escala_max, limite_faltas_pct, redondeo_desde))
        c_id = cursor.lastrowid
        conn.commit()
        registrar_historial("cursos", c_id, "nombre", None, f"{nom_clean} - {sec_clean}", "CREAR", db_path)
        return c_id, True

def crear_curso(
    periodo_id: int,
    nombre: str,
    seccion: str,
    nota_minima: float = DEFAULT_NOTA_MINIMA,
    escala_max: float = DEFAULT_ESCALA_MAX,
    limite_faltas_pct: float = DEFAULT_LIMITE_FALTAS_PCT,
    redondeo_desde: float = DEFAULT_REDONDEO_DESDE,
    db_path: str = DB_PATH
) -> int:
    c_id, _ = crear_o_obtener_curso(periodo_id, nombre, seccion, nota_minima, escala_max, limite_faltas_pct, redondeo_desde, db_path)
    return c_id

def actualizar_curso(
    curso_id: int,
    nombre: str,
    seccion: str,
    nota_minima: float,
    escala_max: float,
    limite_faltas_pct: float,
    redondeo_desde: float,
    db_path: str = DB_PATH
):
    with get_connection(db_path) as conn:
        conn.execute("""
        UPDATE cursos
        SET nombre = ?, seccion = ?, nota_minima = ?, escala_max = ?, limite_faltas_pct = ?, redondeo_desde = ?
        WHERE id = ?
        """, (nombre.strip(), seccion.strip(), nota_minima, escala_max, limite_faltas_pct, redondeo_desde, curso_id))
        conn.commit()
        registrar_historial("cursos", curso_id, "configuracion", None, f"{nombre} - {seccion}", "MODIFICAR", db_path)

def cambiar_estado_curso(curso_id: int, activo: bool, db_path: str = DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("UPDATE cursos SET activo = ? WHERE id = ?", (1 if activo else 0, curso_id))
        conn.commit()

def listar_cursos(periodo_id: Optional[int] = None, solo_activos: bool = True, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
        SELECT c.*, p.nombre as periodo_nombre
        FROM cursos c
        JOIN periodos p ON c.periodo_id = p.id
        WHERE 1=1
        """
        params = []
        if solo_activos:
            query += " AND c.activo = 1 AND p.activo = 1"
        if periodo_id:
            query += " AND c.periodo_id = ?"
            params.append(periodo_id)
        query += " ORDER BY c.nombre, c.seccion"
        cursor.execute(query, params)
        return cursor.fetchall()

def obtener_curso_por_id(curso_id: int, db_path: str = DB_PATH) -> Optional[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.*, p.nombre as periodo_nombre
        FROM cursos c
        JOIN periodos p ON c.periodo_id = p.id
        WHERE c.id = ?
        """, (curso_id,))
        return cursor.fetchone()

# --- HORARIOS ---

def agregar_horario(
    curso_id: int,
    dia_semana: int,
    hora_inicio: str,
    hora_fin: str,
    minutos_tolerancia: int = DEFAULT_MINUTOS_TOLERANCIA,
    db_path: str = DB_PATH
) -> int:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM horarios WHERE curso_id = ? AND dia_semana = ? AND hora_inicio = ?", (curso_id, dia_semana, hora_inicio))
        row = cursor.fetchone()
        if row:
            return row['id']

        cursor.execute("""
        INSERT INTO horarios (curso_id, dia_semana, hora_inicio, hora_fin, minutos_tolerancia)
        VALUES (?, ?, ?, ?, ?)
        """, (curso_id, dia_semana, hora_inicio, hora_fin, minutos_tolerancia))
        horario_id = cursor.lastrowid
        conn.commit()
        return horario_id

def eliminar_horario(horario_id: int, db_path: str = DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM horarios WHERE id = ?", (horario_id,))
        conn.commit()

def listar_horarios_curso(curso_id: int, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM horarios WHERE curso_id = ? ORDER BY dia_semana, hora_inicio", (curso_id,))
        return cursor.fetchall()

def obtener_clases_del_dia(fecha: Optional[datetime] = None, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    if fecha is None:
        fecha = datetime.now()

    dia_semana = fecha.weekday()
    fecha_str = fecha.strftime("%Y-%m-%d")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT h.*, c.nombre as curso_nombre, c.seccion, c.id as curso_id,
               s.id as sesion_id, s.estado as sesion_estado
        FROM horarios h
        JOIN cursos c ON h.curso_id = c.id
        JOIN periodos p ON c.periodo_id = p.id
        LEFT JOIN sesiones_asistencia s ON (s.curso_id = c.id AND s.fecha = ?)
        WHERE h.dia_semana = ? AND c.activo = 1 AND p.activo = 1
        ORDER BY h.hora_inicio
        """, (fecha_str, dia_semana))
        return cursor.fetchall()
