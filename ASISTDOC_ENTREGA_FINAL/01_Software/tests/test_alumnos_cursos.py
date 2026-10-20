import pytest
import os
import tempfile
import pandas as pd
from database import init_db
from cursos import crear_periodo, listar_periodos, crear_curso, listar_cursos, agregar_horario, obtener_clases_del_dia
from alumnos import crear_o_obtener_alumno, matricular_alumno, listar_alumnos_curso, buscar_alumnos_en_curso, importar_alumnos_df
from utils import normalize_text

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_periodos_y_cursos(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    periodos = listar_periodos(db_path=temp_db)
    assert len(periodos) == 1
    assert periodos[0]['nombre'] == "2026-II"

    c_id = crear_curso(p_id, "Redes II", "Sección A", db_path=temp_db)
    cursos = listar_cursos(periodo_id=p_id, db_path=temp_db)
    assert len(cursos) == 1
    assert cursos[0]['nombre'] == "Redes II"

def test_alumnos_y_busqueda_normalizada(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)

    a1_id, _ = crear_o_obtener_alumno("2026001", "José Pérez", db_path=temp_db)
    a2_id, _ = crear_o_obtener_alumno("2026002", "María Gómez", db_path=temp_db)

    matricular_alumno(a1_id, c_id, db_path=temp_db)
    matricular_alumno(a2_id, c_id, db_path=temp_db)

    alumnos = listar_alumnos_curso(c_id, db_path=temp_db)
    assert len(alumnos) == 2

    # Búsqueda normalizada sin tildes ni mayúsculas
    res1 = buscar_alumnos_en_curso(c_id, "perez", db_path=temp_db)
    assert len(res1) == 1
    assert res1[0]['nombre'] == "José Pérez"

    res2 = buscar_alumnos_en_curso(c_id, "maria", db_path=temp_db)
    assert len(res2) == 1
    assert res2[0]['nombre'] == "María Gómez"

def test_importar_alumnos_df(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Base de Datos", "B", db_path=temp_db)

    df = pd.DataFrame([
        {"codigo": "2026010", "nombre": "Carlos Mamani"},
        {"codigo": "2026011", "nombre": "Ana Ruiz"},
        {"codigo": "", "nombre": "Invalido"}, # Inválido
        {"codigo": "2026010", "nombre": "Carlos Mamani"} # Duplicado
    ])

    res = importar_alumnos_df(df, c_id, db_path=temp_db)
    assert res["exitosos"] == 2
    assert res["duplicados_curso"] == 1
    assert res["invalidos"] == 1
