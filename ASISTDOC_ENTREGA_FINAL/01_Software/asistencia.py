import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from database import get_connection, DB_PATH, registrar_historial
from config import DEFAULT_MINUTOS_TOLERANCIA
from alumnos import listar_alumnos_curso

def obtener_o_crear_sesion(
    curso_id: int,
    fecha: Optional[str] = None, # YYYY-MM-DD
    hora_inicio: Optional[str] = None, # HH:MM
    db_path: str = DB_PATH
) -> Tuple[int, str]:
    """
    Obtiene la sesión existente o crea una nueva para la fecha dada.
    Retorna (sesion_id, estado).
    """
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    if not hora_inicio:
        hora_inicio = datetime.now().strftime("%H:%M")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, estado FROM sesiones_asistencia WHERE curso_id = ? AND fecha = ?", (curso_id, fecha))
        row = cursor.fetchone()
        if row:
            return row['id'], row['estado']

        cursor.execute("""
        INSERT INTO sesiones_asistencia (curso_id, fecha, hora_inicio, estado)
        VALUES (?, ?, ?, 'abierta')
        """, (curso_id, fecha, hora_inicio))
        sesion_id = cursor.lastrowid
        conn.commit()

        # Inicializar todos los alumnos matriculados como sin registrar o pendientes
        registrar_historial("sesiones_asistencia", sesion_id, "estado", None, "abierta", "CREAR", db_path)
        return sesion_id, 'abierta'

def marcar_todos_presentes(sesion_id: int, hora_llegada: Optional[str] = None, db_path: str = DB_PATH):
    """
    Marca a todos los alumnos matriculados en el curso como 'presente' si aún no tienen asistencia registrada.
    """
    if not hora_llegada:
        hora_llegada = datetime.now().strftime("%H:%M:%S")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT curso_id, estado FROM sesiones_asistencia WHERE id = ?", (sesion_id,))
        sesion = cursor.fetchone()
        if not sesion or sesion['estado'] == 'cerrada':
            raise ValueError("La sesión no existe o está cerrada.")

        alumnos = listar_alumnos_curso(sesion['curso_id'], solo_activos=True, db_path=db_path)
        for a in alumnos:
            cursor.execute("""
            INSERT INTO asistencias (sesion_id, alumno_id, hora_llegada, estado, nota_texto)
            VALUES (?, ?, ?, 'presente', '')
            ON CONFLICT(sesion_id, alumno_id) DO UPDATE SET
                estado = 'presente',
                hora_llegada = excluded.hora_llegada
            """, (sesion_id, a['id'], hora_llegada))
        conn.commit()

def registrar_asistencia_individual(
    sesion_id: int,
    alumno_id: int,
    estado: str, # presente, tardanza, falta, justificada
    hora_llegada: Optional[str] = None,
    nota_texto: str = "",
    auto_calcular_tardanza: bool = True,
    db_path: str = DB_PATH
) -> str:
    """
    Registra o actualiza la asistencia de un alumno individual.
    Si auto_calcular_tardanza es True y el estado ingresado es 'presente',
    verifica si excede hora_inicio + tolerancia.
    """
    if estado not in ['presente', 'tardanza', 'falta', 'justificada']:
        raise ValueError(f"Estado de asistencia inválido: {estado}")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT s.*, h.minutos_tolerancia FROM sesiones_asistencia s "
                       "LEFT JOIN horarios h ON h.curso_id = s.curso_id "
                       "WHERE s.id = ?", (sesion_id,))
        sesion = cursor.fetchone()
        if not sesion:
            raise ValueError("Sesión no encontrada.")

        # Obtener valor anterior si existe
        cursor.execute("SELECT estado FROM asistencias WHERE sesion_id = ? AND alumno_id = ?", (sesion_id, alumno_id))
        asist_prev = cursor.fetchone()
        valor_anterior = asist_prev['estado'] if asist_prev else None

        # Cálculo automático de tardanza
        estado_final = estado
        if auto_calcular_tardanza and estado == 'presente' and sesion['hora_inicio']:
            tolerancia = sesion['minutos_tolerancia'] if sesion['minutos_tolerancia'] is not None else DEFAULT_MINUTOS_TOLERANCIA
            try:
                hora_sesion = datetime.strptime(sesion['hora_inicio'], "%H:%M")
                hora_limite = hora_sesion + timedelta(minutes=tolerancia)

                now_time = datetime.now()
                hora_llegada_obj = datetime.strptime(hora_llegada, "%H:%M:%S") if hora_llegada else now_time
                # Comparar solo horas y minutos
                time_limite = hora_limite.time()
                time_llegada = hora_llegada_obj.time()

                if time_llegada > time_limite:
                    estado_final = 'tardanza'
            except Exception:
                pass

        if not hora_llegada and estado_final in ['presente', 'tardanza']:
            hora_llegada = datetime.now().strftime("%H:%M:%S")

        cursor.execute("""
        INSERT INTO asistencias (sesion_id, alumno_id, hora_llegada, estado, nota_texto)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(sesion_id, alumno_id) DO UPDATE SET
            estado = excluded.estado,
            hora_llegada = excluded.hora_llegada,
            nota_texto = excluded.nota_texto
        """, (sesion_id, alumno_id, hora_llegada, estado_final, nota_texto))
        conn.commit()

        accion = "MODIFICAR" if valor_anterior else "CREAR"
        registrar_historial("asistencias", sesion_id, f"alumno_{alumno_id}", valor_anterior, estado_final, accion, db_path)
        return estado_final

def cerrar_sesion_asistencia(
    sesion_id: int,
    marcar_sin_registro_como_falta: bool = True,
    db_path: str = DB_PATH
) -> Dict[str, int]:
    """
    Cierra la sesión de asistencia. Opcionalmente marca a todos los alumnos sin registro como 'falta'.
    """
    hora_cierre = datetime.now().strftime("%H:%M")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT curso_id, estado FROM sesiones_asistencia WHERE id = ?", (sesion_id,))
        sesion = cursor.fetchone()
        if not sesion:
            raise ValueError("Sesión no encontrada.")

        curso_id = sesion['curso_id']
        alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)

        if marcar_sin_registro_como_falta:
            for a in alumnos:
                cursor.execute("SELECT id FROM asistencias WHERE sesion_id = ? AND alumno_id = ?", (sesion_id, a['id']))
                if not cursor.fetchone():
                    cursor.execute("""
                    INSERT INTO asistencias (sesion_id, alumno_id, hora_llegada, estado, nota_texto)
                    VALUES (?, ?, NULL, 'falta', 'Marcado automático al cerrar sesión')
                    """, (sesion_id, a['id']))

        cursor.execute("""
        UPDATE sesiones_asistencia
        SET estado = 'cerrada', hora_cierre = ?
        WHERE id = ?
        """, (hora_cierre, sesion_id))
        conn.commit()

        registrar_historial("sesiones_asistencia", sesion_id, "estado", sesion['estado'], "cerrada", "MODIFICAR", db_path)

        # Resumen de conteo
        cursor.execute("SELECT estado, COUNT(*) as cant FROM asistencias WHERE sesion_id = ? GROUP BY estado", (sesion_id,))
        rows = cursor.fetchall()
        resumen = {r['estado']: r['cant'] for r in rows}
        return resumen

def abrir_sesion_para_correccion(sesion_id: int, db_path: str = DB_PATH):
    """
    Abre explícitamente una sesión cerrada para permitir correcciones supervisadas.
    """
    with get_connection(db_path) as conn:
        conn.execute("UPDATE sesiones_asistencia SET estado = 'abierta' WHERE id = ?", (sesion_id,))
        conn.commit()
        registrar_historial("sesiones_asistencia", sesion_id, "estado", "cerrada", "abierta", "MODIFICAR", db_path)

def obtener_resumen_asistencia_sesion(sesion_id: int, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    """
    Obtiene la lista completa de alumnos de un curso con su registro de asistencia en la sesión.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT a.id as alumno_id, a.codigo, a.nombre,
               ast.id as asistencia_id, ast.estado, ast.hora_llegada, ast.nota_texto
        FROM sesiones_asistencia s
        JOIN matriculas m ON s.curso_id = m.curso_id AND m.activo = 1
        JOIN alumnos a ON m.alumno_id = a.id AND a.activo = 1
        LEFT JOIN asistencias ast ON (ast.sesion_id = s.id AND ast.alumno_id = a.id)
        WHERE s.id = ?
        ORDER BY a.nombre
        """, (sesion_id,))
        return cursor.fetchall()
