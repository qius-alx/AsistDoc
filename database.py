import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from utils import get_logger

DB_PATH = os.path.join("data", "asistdoc.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Crea y retorna una conexión a SQLite habilitando claves foráneas.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = DB_PATH):
    """
    Inicializa las tablas e índices de la base de datos si no existen.
    """
    logger = get_logger()
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()

            # 1. Tabla periodos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS periodos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
            );
            """)

            # 2. Tabla cursos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                periodo_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                seccion TEXT NOT NULL,
                nota_minima REAL NOT NULL DEFAULT 11.0 CHECK (nota_minima >= 0),
                escala_max REAL NOT NULL DEFAULT 20.0 CHECK (escala_max > 0),
                limite_faltas_pct REAL NOT NULL DEFAULT 30.0 CHECK (limite_faltas_pct BETWEEN 0 AND 100),
                redondeo_desde REAL NOT NULL DEFAULT 0.5 CHECK (redondeo_desde BETWEEN 0 AND 1),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                FOREIGN KEY (periodo_id) REFERENCES periodos(id) ON DELETE RESTRICT,
                UNIQUE (periodo_id, nombre, seccion)
            );
            """)

            # 3. Tabla horarios
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                minutos_tolerancia INTEGER NOT NULL DEFAULT 10 CHECK (minutos_tolerancia >= 0),
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE
            );
            """)

            # 4. Tabla alumnos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
            );
            """)

            # 5. Tabla matriculas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS matriculas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                curso_id INTEGER NOT NULL,
                fecha_matricula TEXT NOT NULL DEFAULT (DATE('now')),
                activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE RESTRICT,
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE RESTRICT,
                UNIQUE (alumno_id, curso_id)
            );
            """)

            # 6. Tabla sesiones_asistencia
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones_asistencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                fecha TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_cierre TEXT,
                estado TEXT NOT NULL DEFAULT 'abierta' CHECK (estado IN ('abierta', 'cerrada')),
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE RESTRICT,
                UNIQUE (curso_id, fecha)
            );
            """)

            # 7. Tabla asistencias
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                alumno_id INTEGER NOT NULL,
                hora_llegada TEXT,
                estado TEXT NOT NULL CHECK (estado IN ('presente', 'tardanza', 'falta', 'justificada')),
                nota_texto TEXT DEFAULT '',
                FOREIGN KEY (sesion_id) REFERENCES sesiones_asistencia(id) ON DELETE CASCADE,
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE RESTRICT,
                UNIQUE (sesion_id, alumno_id)
            );
            """)

            # 8. Tabla evaluaciones
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                peso REAL NOT NULL CHECK (peso > 0 AND peso <= 100),
                fecha TEXT,
                orden INTEGER NOT NULL DEFAULT 1,
                activa INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1)),
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE,
                UNIQUE (curso_id, nombre)
            );
            """)

            # 9. Tabla notas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alumno_id INTEGER NOT NULL,
                evaluacion_id INTEGER NOT NULL,
                valor REAL CHECK (valor IS NULL OR (valor >= 0 AND valor <= 20)),
                estado TEXT NOT NULL DEFAULT 'registrada' CHECK (estado IN ('registrada', 'NP', 'pendiente')),
                fecha_modificacion TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime')),
                FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE RESTRICT,
                FOREIGN KEY (evaluacion_id) REFERENCES evaluaciones(id) ON DELETE CASCADE,
                UNIQUE (alumno_id, evaluacion_id)
            );
            """)

            # 10. Tabla historial
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabla TEXT NOT NULL,
                registro_id INTEGER NOT NULL,
                campo TEXT NOT NULL,
                valor_anterior TEXT,
                valor_nuevo TEXT,
                accion TEXT NOT NULL CHECK (accion IN ('CREAR', 'MODIFICAR', 'ELIMINAR', 'RESTAURAR')),
                fecha_hora TEXT NOT NULL DEFAULT (DATETIME('now', 'localtime'))
            );
            """)

            # 11. Tabla configuracion
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );
            """)

            # CREACIÓN DE ÍNDICES DE RENDIMIENTO
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cursos_periodo ON cursos(periodo_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matriculas_curso ON matriculas(curso_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_matriculas_alumno ON matriculas(alumno_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sesiones_curso_fecha ON sesiones_asistencia(curso_id, fecha);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asistencias_sesion ON asistencias(sesion_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_asistencias_alumno ON asistencias(alumno_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evaluaciones_curso ON evaluaciones(curso_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notas_evaluacion ON notas(evaluacion_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notas_alumno ON notas(alumno_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alumnos_codigo ON alumnos(codigo);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_tabla_reg ON historial(tabla, registro_id);")

            conn.commit()
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        raise e

def registrar_historial(tabla: str, registro_id: int, campo: str, valor_anterior: Optional[str], valor_nuevo: Optional[str], accion: str, db_path: str = DB_PATH):
    """
    Registra un evento en la tabla de auditoría historial.
    """
    with get_connection(db_path) as conn:
        conn.execute("""
        INSERT INTO historial (tabla, registro_id, campo, valor_anterior, valor_nuevo, accion)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (tabla, registro_id, campo, valor_anterior, valor_nuevo, accion))
        conn.commit()

def obtener_historial_reciente(limite: int = 50, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    """
    Retorna los registros más recientes del historial.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM historial ORDER BY id DESC LIMIT ?", (limite,))
        return cursor.fetchall()
