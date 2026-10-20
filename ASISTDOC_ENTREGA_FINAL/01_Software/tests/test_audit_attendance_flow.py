import pytest
import os
import tempfile
from database import init_db, obtener_historial_reciente
from cursos import crear_periodo, crear_curso, agregar_horario
from alumnos import crear_o_obtener_alumno, matricular_alumno
from asistencia import (
    obtener_o_crear_sesion, marcar_todos_presentes, registrar_asistencia_individual,
    cerrar_sesion_asistencia, abrir_sesion_para_correccion
)

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_attendance_tardiness_closed_session_flow(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)
    agregar_horario(c_id, dia_semana=0, hora_inicio="08:00", hora_fin="10:00", minutos_tolerancia=10, db_path=temp_db)

    a1_id, _ = crear_o_obtener_alumno("2026001", "Juan Perez", db_path=temp_db)
    a2_id, _ = crear_o_obtener_alumno("2026002", "Ana Gomez", db_path=temp_db)
    a3_id, _ = crear_o_obtener_alumno("2026003", "Pedro Soto", db_path=temp_db)

    matricular_alumno(a1_id, c_id, db_path=temp_db)
    matricular_alumno(a2_id, c_id, db_path=temp_db)
    matricular_alumno(a3_id, c_id, db_path=temp_db)

    s_id, estado = obtener_o_crear_sesion(c_id, fecha="2026-10-20", hora_inicio="08:00", db_path=temp_db)
    assert estado == 'abierta'

    # Check arrival times vs tolerancia (08:00 + 10min = 08:10 max)
    # 08:05 -> presente
    e1 = registrar_asistencia_individual(s_id, a1_id, estado='presente', hora_llegada='08:05:00', auto_calcular_tardanza=True, db_path=temp_db)
    assert e1 == 'presente'

    # 08:10 -> presente
    e2 = registrar_asistencia_individual(s_id, a2_id, estado='presente', hora_llegada='08:10:00', auto_calcular_tardanza=True, db_path=temp_db)
    assert e2 == 'presente'

    # 08:11 -> tardanza
    e3 = registrar_asistencia_individual(s_id, a3_id, estado='presente', hora_llegada='08:11:00', auto_calcular_tardanza=True, db_path=temp_db)
    assert e3 == 'tardanza'

    # Close session
    cerrar_sesion_asistencia(s_id, db_path=temp_db)

    # Reopen explicitly for correction and check history
    abrir_sesion_para_correccion(s_id, db_path=temp_db)
    registrar_asistencia_individual(s_id, a3_id, estado='justificada', nota_texto='Médico', db_path=temp_db)

    hist = obtener_historial_reciente(10, temp_db)
    assert len(hist) > 0
    assert any(h['tabla'] == 'asistencias' for h in hist)
