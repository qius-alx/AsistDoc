import pytest
import os
import tempfile
import pandas as pd
from database import init_db
from cursos import crear_periodo, crear_curso
from alumnos import (
    crear_o_obtener_alumno, matricular_alumno,
    listar_alumnos_curso, buscar_alumnos_en_curso, importar_alumnos_df
)
from utils import normalize_text

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)

def test_search_normalization_edge_cases(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Redes II", "A", db_path=temp_db)

    a1_id, _ = crear_o_obtener_alumno("2026001", "José Pérez Mamani", db_path=temp_db)
    a2_id, _ = crear_o_obtener_alumno("2026002", "María Núñez", db_path=temp_db)
    matricular_alumno(a1_id, c_id, db_path=temp_db)
    matricular_alumno(a2_id, c_id, db_path=temp_db)

    # Search queries: 'jose', 'José', 'PEREZ', 'perez', 'mamani'
    for q in ['jose', 'José', 'PEREZ', 'perez', 'mamani']:
        res = buscar_alumnos_en_curso(c_id, q, db_path=temp_db)
        assert len(res) == 1
        assert res[0]['id'] == a1_id

    # Search query: 'nunez', 'Núñez', 'maria'
    for q in ['nunez', 'Núñez', 'maria']:
        res = buscar_alumnos_en_curso(c_id, q, db_path=temp_db)
        assert len(res) == 1
        assert res[0]['id'] == a2_id

    # Search query: '2026' -> Matches both
    res_both = buscar_alumnos_en_curso(c_id, '2026', db_path=temp_db)
    assert len(res_both) == 2

    # Search query: 'inexistente' -> 0 matches
    assert len(buscar_alumnos_en_curso(c_id, 'inexistente', db_path=temp_db)) == 0

    # Empty search query -> Returns all
    assert len(buscar_alumnos_en_curso(c_id, '', db_path=temp_db)) == 2

def test_import_dataframe_edge_cases(temp_db):
    p_id = crear_periodo("2026-II", "2026-08-01", "2026-12-15", db_path=temp_db)
    c_id = crear_curso(p_id, "Base de Datos", "A", db_path=temp_db)

    # Caso A: Correct File with tildes and spaces
    df_a = pd.DataFrame([
        {"codigo": " 2026090 ", "nombre": "  José Pérez  "},
        {"codigo": "2026091", "nombre": "María Núñez"}
    ])
    res_a = importar_alumnos_df(df_a, c_id, db_path=temp_db)
    assert res_a["exitosos"] == 2

    # Caso B: Missing 'codigo' column
    df_b = pd.DataFrame([{"nombre": "Carlos Soto"}])
    res_b = importar_alumnos_df(df_b, c_id, db_path=temp_db)
    assert len(res_b["errores"]) > 0

    # Caso C: Missing 'nombre' column
    df_c = pd.DataFrame([{"codigo": "2026099"}])
    res_c = importar_alumnos_df(df_c, c_id, db_path=temp_db)
    assert len(res_c["errores"]) > 0

    # Caso D: Duplicate codes in import file
    df_d = pd.DataFrame([
        {"codigo": "2026092", "nombre": "Ana Gomez"},
        {"codigo": "2026092", "nombre": "Ana Gomez"}
    ])
    res_d = importar_alumnos_df(df_d, c_id, db_path=temp_db)
    assert res_d["exitosos"] == 1
    assert res_d["duplicados_curso"] == 1

    # Caso E: Empty DataFrame
    df_e = pd.DataFrame(columns=["codigo", "nombre"])
    res_e = importar_alumnos_df(df_e, c_id, db_path=temp_db)
    assert res_e["exitosos"] == 0
