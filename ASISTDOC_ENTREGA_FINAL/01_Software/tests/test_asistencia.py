import pytest
import os
import tempfile
import sqlite3
from database import init_db, get_connection
from cursos import crear_periodo, crear_curso, agregar_horario
from alumnos import crear_o_obtener_alumno, matricular_alumno
from asistencia import (
    obtener_o_crear_sesion,
    marcar_todos_presentes,
    registrar_asistencia_individual,
    cerrar_sesion_asistencia,
    abrir_sesion_para_correccion,
    obtener_resumen_asistencia_sesion
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_flujo_asistencia_y_restricciones(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)
    agregar_horario(c_id, 0, "08:00", "10:00", minutos_tolerancia=10, db_path=temp_db)

    a1_id, _ = crear_o_obtener_alumno("2026001", "Juan Pérez", db_path=temp_db)
    a2_id, _ = crear_o_obtener_alumno("2026002", "Ana Gómez", db_path=temp_db)
    matricular_alumno(a1_id, c_id, db_path=temp_db)
    matricular_alumno(a2_id, c_id, db_path=temp_db)

    # 1. Crear / Obtener Sesión
    sesion_id, estado = obtener_o_crear_sesion(c_id, fecha="2026-10-20", hora_inicio="08:00", db_path=temp_db)
    assert estado == 'abierta'

    # Sesión duplicada para la misma fecha -> Debe retornar la misma sesión existente
    sesion_id_dup, _ = obtener_o_crear_sesion(c_id, fecha="2026-10-20", db_path=temp_db)
    assert sesion_id == sesion_id_dup

    # 2. Marcar Todos Presentes
    marcar_todos_presentes(sesion_id, hora_llegada="08:05:00", db_path=temp_db)
    resumen = obtener_resumen_asistencia_sesion(sesion_id, db_path=temp_db)
    assert len(resumen) == 2
    assert resumen[0]['estado'] == 'presente'
    assert resumen[1]['estado'] == 'presente'

    # 3. Cambio individual a Tardanza / Falta
    # Cálculo de tardanza: llegada 08:15 cuando inicio era 08:00 y tolerancia 10min -> tardanza
    est = registrar_asistencia_individual(
        sesion_id, a2_id, estado='presente', hora_llegada='08:15:00',
        auto_calcular_tardanza=True, db_path=temp_db
    )
    assert est == 'tardanza'

    # 4. Restricción UNIQUE(sesion_id, alumno_id) en SQLite
    conn = get_connection(temp_db)
    cursor = conn.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO asistencias (sesion_id, alumno_id, estado) VALUES (?, ?, 'presente')", (sesion_id, a1_id))
    conn.close()

    # 5. Cierre de Sesión
    resumen_cierre = cerrar_sesion_asistencia(sesion_id, marcar_sin_registro_como_falta=True, db_path=temp_db)
    assert 'presente' in resumen_cierre
    assert 'tardanza' in resumen_cierre

    # Intentar modificar sesión cerrada debe poder reabrirse previa acción explícita
    abrir_sesion_para_correccion(sesion_id, db_path=temp_db)
    _, est_reabierta = obtener_o_crear_sesion(c_id, fecha="2026-10-20", db_path=temp_db)
    assert est_reabierta == 'abierta'
