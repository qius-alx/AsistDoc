import sqlite3
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
from database import get_connection, DB_PATH, registrar_historial
from utils import format_nota
from cursos import obtener_curso_por_id
from alumnos import listar_alumnos_curso

# --- EVALUACIONES ---

def crear_evaluacion(
    curso_id: int,
    nombre: str,
    peso: float,
    fecha: Optional[str] = None,
    orden: int = 1,
    db_path: str = DB_PATH
) -> int:
    if peso <= 0 or peso > 100:
        raise ValueError("El peso debe ser mayor a 0% y menor o igual a 100%.")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO evaluaciones (curso_id, nombre, peso, fecha, orden, activa)
        VALUES (?, ?, ?, ?, ?, 1)
        """, (curso_id, nombre.strip(), peso, fecha, orden))
        eval_id = cursor.lastrowid
        conn.commit()
        registrar_historial("evaluaciones", eval_id, "nombre", None, nombre, "CREAR", db_path)
        return eval_id

def actualizar_evaluacion(
    evaluacion_id: int,
    nombre: str,
    peso: float,
    fecha: Optional[str] = None,
    orden: int = 1,
    db_path: str = DB_PATH
):
    if peso <= 0 or peso > 100:
        raise ValueError("El peso debe ser mayor a 0% y menor o igual a 100%.")

    with get_connection(db_path) as conn:
        conn.execute("""
        UPDATE evaluaciones
        SET nombre = ?, peso = ?, fecha = ?, orden = ?
        WHERE id = ?
        """, (nombre.strip(), peso, fecha, orden, evaluacion_id))
        conn.commit()
        registrar_historial("evaluaciones", evaluacion_id, "peso", None, str(peso), "MODIFICAR", db_path)

def desactivar_evaluacion(evaluacion_id: int, db_path: str = DB_PATH):
    with get_connection(db_path) as conn:
        conn.execute("UPDATE evaluaciones SET activa = 0 WHERE id = ?", (evaluacion_id,))
        conn.commit()
        registrar_historial("evaluaciones", evaluacion_id, "activa", "1", "0", "MODIFICAR", db_path)

def listar_evaluaciones_curso(curso_id: int, solo_activas: bool = True, db_path: str = DB_PATH) -> List[sqlite3.Row]:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM evaluaciones WHERE curso_id = ?"
        if solo_activas:
            query += " AND activa = 1"
        query += " ORDER BY orden, id"
        cursor.execute(query, (curso_id,))
        return cursor.fetchall()

def verificar_suma_pesos(curso_id: int, db_path: str = DB_PATH) -> Tuple[float, bool]:
    """
    Retorna (suma_pesos, es_cien_por_ciento).
    """
    evals = listar_evaluaciones_curso(curso_id, solo_activas=True, db_path=db_path)
    suma = sum(e['peso'] for e in evals)
    return round(suma, 2), abs(suma - 100.0) < 0.01

def copiar_evaluaciones_entre_cursos(curso_origen_id: int, curso_destino_id: int, db_path: str = DB_PATH):
    evals = listar_evaluaciones_curso(curso_origen_id, solo_activas=True, db_path=db_path)
    for e in evals:
        try:
            crear_evaluacion(curso_destino_id, e['nombre'], e['peso'], e['fecha'], e['orden'], db_path=db_path)
        except sqlite3.IntegrityError:
            pass # Ignorar duplicados de nombre

# --- REGISTRO Y VALIDACIÓN DE NOTAS ---

def registrar_o_actualizar_nota(
    alumno_id: int,
    evaluacion_id: int,
    valor: Optional[float] = None,
    estado: str = 'registrada', # registrada, NP, pendiente
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Registra o actualiza la nota de un alumno en una evaluación.
    Aplica validaciones rigurosas de rango y estado.
    """
    if estado not in ['registrada', 'NP', 'pendiente']:
        raise ValueError(f"Estado de nota inválido: {estado}")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Obtener escala_max del curso al que pertenece la evaluación
        cursor.execute("""
        SELECT e.curso_id, c.escala_max, e.nombre as eval_nombre
        FROM evaluaciones e
        JOIN cursos c ON e.curso_id = c.id
        WHERE e.id = ?
        """, (evaluacion_id,))
        eval_info = cursor.fetchone()
        if not eval_info:
            raise ValueError("Evaluación no encontrada.")

        escala_max = eval_info['escala_max']

        # Validaciones de valor
        if estado == 'registrada':
            if valor is None:
                raise ValueError("Para el estado 'registrada' debe proporcionar un valor numérico.")
            valor = float(valor)
            if valor < 0 or valor > escala_max:
                raise ValueError(f"La nota debe estar entre 0.0 y {escala_max:.1f}.")
        else: # NP o pendiente
            valor = None

        # Obtener valor anterior para historial
        cursor.execute("SELECT valor, estado FROM notas WHERE alumno_id = ? AND evaluacion_id = ?", (alumno_id, evaluacion_id))
        prev = cursor.fetchone()
        val_anterior_str = f"{prev['valor']} ({prev['estado']})" if prev else "None"

        cursor.execute("""
        INSERT INTO notas (alumno_id, evaluacion_id, valor, estado, fecha_modificacion)
        VALUES (?, ?, ?, ?, DATETIME('now', 'localtime'))
        ON CONFLICT(alumno_id, evaluacion_id) DO UPDATE SET
            valor = excluded.valor,
            estado = excluded.estado,
            fecha_modificacion = DATETIME('now', 'localtime')
        """, (alumno_id, evaluacion_id, valor, estado))
        conn.commit()

        val_nuevo_str = f"{valor} ({estado})"
        registrar_historial("notas", evaluacion_id, f"alumno_{alumno_id}", val_anterior_str, val_nuevo_str, "MODIFICAR" if prev else "CREAR", db_path)

        return {"alumno_id": alumno_id, "evaluacion_id": evaluacion_id, "valor": valor, "estado": estado}

def deshacer_ultimo_ingreso_nota(curso_id: int, db_path: str = DB_PATH) -> bool:
    """
    Deshace el último ingreso de nota realizado en el curso consultando la tabla historial.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT h.*, e.id as eval_id
        FROM historial h
        JOIN evaluaciones e ON h.registro_id = e.id
        WHERE h.tabla = 'notas' AND e.curso_id = ?
        ORDER BY h.id DESC LIMIT 1
        """, (curso_id,))
        row = cursor.fetchone()
        if not row:
            return False

        # Extraer alumno_id de campo 'alumno_X'
        try:
            alumno_id = int(row['campo'].replace('alumno_', ''))
            eval_id = row['registro_id']
            val_ant_str = row['valor_anterior']

            if val_ant_str == "None" or not val_ant_str:
                cursor.execute("DELETE FROM notas WHERE alumno_id = ? AND evaluacion_id = ?", (alumno_id, eval_id))
            else:
                # Parsear anterior ej: "15.0 (registrada)" o "None (NP)"
                parts = val_ant_str.split(" ")
                val_val = float(parts[0]) if parts[0] != "None" else None
                est_val = parts[1].replace("(", "").replace(")", "")
                cursor.execute("UPDATE notas SET valor = ?, estado = ? WHERE alumno_id = ? AND evaluacion_id = ?",
                               (val_val, est_val, alumno_id, eval_id))

            # Registrar el hecho de deshacer en historial
            cursor.execute("DELETE FROM historial WHERE id = ?", (row['id'],))
            conn.commit()
            return True
        except Exception:
            return False

# --- CÁLCULOS ACADÉMICOS ---

def calcular_promedio_alumno(
    alumno_id: int,
    curso_id: int,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Calcula el promedio ponderado del alumno.
    NP cuenta como 0.0 en el promedio.
    Aplica regla de redondeo configurada en el curso.
    """
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    if not curso:
        raise ValueError("Curso no encontrado.")

    nota_minima = curso['nota_minima']
    redondeo_desde = curso['redondeo_desde']

    evaluaciones = listar_evaluaciones_curso(curso_id, solo_activas=True, db_path=db_path)
    if not evaluaciones:
        return {"promedio_raw": 0.0, "promedio_final": 0.0, "condicion": "Sin Evaluaciones", "completado": False}

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        suma_ponderada = 0.0
        peso_total_evaluado = 0.0
        peso_total_curso = sum(e['peso'] for e in evaluaciones)
        pendientes = 0

        for e in evaluaciones:
            cursor.execute("SELECT valor, estado FROM notas WHERE alumno_id = ? AND evaluacion_id = ?", (alumno_id, e['id']))
            n = cursor.fetchone()

            if not n or n['estado'] == 'pendiente':
                pendientes += 1
            elif n['estado'] == 'NP':
                # NP equivale a 0.0
                suma_ponderada += 0.0 * (e['peso'] / 100.0)
                peso_total_evaluado += e['peso']
            elif n['estado'] == 'registrada' and n['valor'] is not None:
                suma_ponderada += n['valor'] * (e['peso'] / 100.0)
                peso_total_evaluado += e['peso']

        # Normalizar si no todas las evaluaciones se han tomado aún
        if peso_total_evaluado > 0:
            promedio_raw = (suma_ponderada / (peso_total_evaluado / 100.0))
        else:
            promedio_raw = 0.0

        # Regla de Redondeo
        # Tradicional: si la parte decimal >= redondeo_desde, redondea arriba
        entero = int(promedio_raw)
        decimal = promedio_raw - entero
        if decimal >= redondeo_desde:
            promedio_final = float(entero + 1)
        else:
            promedio_final = float(entero)

        condicion = "APROBADO" if promedio_final >= nota_minima else "DESAPROBADO"
        if pendientes > 0 and promedio_final < nota_minima:
            condicion = "EN PROCESO"

        return {
            "promedio_raw": round(promedio_raw, 2),
            "promedio_final": promedio_final,
            "condicion": condicion,
            "pendientes": pendientes,
            "completado": (pendientes == 0)
        }

def calcular_nota_necesaria(
    alumno_id: int,
    curso_id: int,
    evaluacion_pendiente_id: int,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """
    Calcula cuánto necesita obtener un estudiante en una evaluación pendiente para alcanzar la nota mínima.

    Fórmula:
    Sea N_min = nota_minima del curso.
    Suma_Actual = sum(nota_i * (peso_i / 100)) para evaluaciones rendidas (NP = 0).
    Peso_Pendiente = peso de la evaluación elegida.
    Nota_Requerida X satisface: Suma_Actual + X * (Peso_Pendiente / 100) >= N_min
    Despejando: X = (N_min - Suma_Actual) / (Peso_Pendiente / 100)
    """
    curso = obtener_curso_por_id(curso_id, db_path=db_path)
    if not curso:
        raise ValueError("Curso no encontrado.")

    nota_minima = curso['nota_minima']
    escala_max = curso['escala_max']

    evaluaciones = listar_evaluaciones_curso(curso_id, solo_activas=True, db_path=db_path)
    eval_target = next((e for e in evaluaciones if e['id'] == evaluacion_pendiente_id), None)
    if not eval_target:
        raise ValueError("Evaluación pendiente no válida.")

    peso_target = eval_target['peso']

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        suma_actual = 0.0

        for e in evaluaciones:
            if e['id'] == evaluacion_pendiente_id:
                continue

            cursor.execute("SELECT valor, estado FROM notas WHERE alumno_id = ? AND evaluacion_id = ?", (alumno_id, e['id']))
            n = cursor.fetchone()
            if n and n['estado'] == 'registrada' and n['valor'] is not None:
                suma_actual += n['valor'] * (e['peso'] / 100.0)
            elif n and n['estado'] == 'NP':
                suma_actual += 0.0

        # Cálculo de nota requerida
        diferencia = nota_minima - suma_actual
        if diferencia <= 0:
            return {
                "nota_necesaria": 0.0,
                "mensaje": "Objetivo alcanzado (ya tiene la nota mínima acumulada).",
                "alcanzable": True
            }

        nota_requerida = diferencia / (peso_target / 100.0)
        nota_requerida_round = round(nota_requerida, 1)

        if nota_requerida_round > escala_max:
            return {
                "nota_necesaria": nota_requerida_round,
                "mensaje": f"No puede alcanzar la nota mínima ({nota_minima}) únicamente con esta evaluación (Requeriría {nota_requerida_round} / {escala_max}).",
                "alcanzable": False
            }

        return {
            "nota_necesaria": nota_requerida_round,
            "mensaje": f"Necesita obtener {nota_requerida_round} sobre {escala_max} en '{eval_target['nombre']}'.",
            "alcanzable": True
        }

def obtener_matriz_notas_curso(curso_id: int, db_path: str = DB_PATH) -> pd.DataFrame:
    """
    Genera el DataFrame dinámico de la acta de notas del curso.
    Columnas: Código | Alumno | [Eval 1] | [Eval 2] ... | Promedio | Condición
    """
    alumnos = listar_alumnos_curso(curso_id, solo_activos=True, db_path=db_path)
    evaluaciones = listar_evaluaciones_curso(curso_id, solo_activas=True, db_path=db_path)

    filas = []
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for a in alumnos:
            fila = {
                "alumno_id": a['id'],
                "Código": a['codigo'],
                "Alumno": a['nombre']
            }
            for e in evaluaciones:
                cursor.execute("SELECT valor, estado FROM notas WHERE alumno_id = ? AND evaluacion_id = ?", (a['id'], e['id']))
                n = cursor.fetchone()
                val_txt = format_nota(n['valor'], n['estado']) if n else '-'
                fila[e['nombre']] = val_txt

            res_prom = calcular_promedio_alumno(a['id'], curso_id, db_path=db_path)
            fila["Promedio"] = res_prom["promedio_final"]
            fila["Condición"] = res_prom["condicion"]
            filas.append(fila)

    df = pd.DataFrame(filas)
    return df
