import os
import random
from database import init_db, DB_PATH
from cursos import crear_periodo, crear_curso, agregar_horario
from alumnos import crear_o_obtener_alumno, matricular_alumno
from asistencia import obtener_o_crear_sesion, registrar_asistencia_individual, cerrar_sesion_asistencia
from notas import crear_evaluacion, registrar_o_actualizar_nota

def poblar_datos_demostracion(db_path: str = DB_PATH):
    print("🌱 Poblando base de datos con información ficticia de demostración...")
    init_db(db_path)

    # 1. Crear Periodo 2026-II
    p_id = crear_periodo("2026-II", "2026-08-15", "2026-12-20", db_path=db_path)

    # 2. Crear Cursos y Horarios
    c1_id = crear_curso(p_id, "Redes II", "Sección A", nota_minima=11.0, limite_faltas_pct=30.0, db_path=db_path)
    c2_id = crear_curso(p_id, "Base de Datos", "Sección B", nota_minima=11.0, limite_faltas_pct=25.0, db_path=db_path)

    agregar_horario(c1_id, dia_semana=0, hora_inicio="08:00", hora_fin="10:00", minutos_tolerancia=10, db_path=db_path)
    agregar_horario(c2_id, dia_semana=1, hora_inicio="10:00", hora_fin="12:00", minutos_tolerancia=15, db_path=db_path)

    # 3. Crear 30 Alumnos Ficticios
    nombres_ficticios = [
        "Carlos Mamani", "Ana Ruiz", "José Pérez", "María Gómez", "Pedro Soto",
        "Lucía Vargas", "Diego Flores", "Sofia Quispe", "Gabriel Mendoza", "Elena Rojas",
        "Mateo Castro", "Camila Paredes", "Javier Morales", "Valeria Espinoza", "Lucas Benitez",
        "Sonia Salazar", "Raúl Gutierrez", "Fiorella Chavez", "Hugo Delgado", "Andrea Silva",
        "Fernando Cabrera", "Claudia Medina", "Gonzalo Navarro", "Daniela Guerrero", "Cesar Ponce",
        "Jimena Rivas", "Oscar Zambrano", "Carmen Montoya", "Guillermo Farfan", "Rosa Acuña"
    ]

    alumnos_ids = []
    for idx, nombre in enumerate(nombres_ficticios, 1):
        codigo = f"2026{idx:04d}"
        a_id, _ = crear_o_obtener_alumno(codigo, nombre, db_path=db_path)
        alumnos_ids.append(a_id)

        matricular_alumno(a_id, c1_id, db_path=db_path)
        if idx <= 20:
            matricular_alumno(a_id, c2_id, db_path=db_path)

    # 4. Crear Evaluaciones para Redes II
    e1_id = crear_evaluacion(c1_id, "Práctica 1", peso=20.0, fecha="2026-09-10", orden=1, db_path=db_path)
    e2_id = crear_evaluacion(c1_id, "Práctica 2", peso=20.0, fecha="2026-10-05", orden=2, db_path=db_path)
    e3_id = crear_evaluacion(c1_id, "Examen Parcial", peso=30.0, fecha="2026-10-25", orden=3, db_path=db_path)
    e4_id = crear_evaluacion(c1_id, "Examen Final", peso=30.0, fecha="2026-12-10", orden=4, db_path=db_path)

    # 5. Registrar Notas con variedad
    for idx, a_id in enumerate(alumnos_ids):
        if idx in [0, 4]: # Alumnos 1 y 5 (Riesgo Alto)
            registrar_o_actualizar_nota(a_id, e1_id, valor=06.0, estado='registrada', db_path=db_path)
            registrar_o_actualizar_nota(a_id, e2_id, valor=08.0, estado='registrada', db_path=db_path)
            registrar_o_actualizar_nota(a_id, e3_id, valor=None, estado='NP', db_path=db_path)
        elif idx in [1, 2]: # NP en Práctica 1
            registrar_o_actualizar_nota(a_id, e1_id, valor=None, estado='NP', db_path=db_path)
            registrar_o_actualizar_nota(a_id, e2_id, valor=15.0, estado='registrada', db_path=db_path)
            registrar_o_actualizar_nota(a_id, e3_id, valor=14.0, estado='registrada', db_path=db_path)
        else: # Regular
            v1 = float((idx % 8) + 11)
            v2 = float(((idx + 3) % 8) + 12)
            registrar_o_actualizar_nota(a_id, e1_id, valor=v1, estado='registrada', db_path=db_path)
            registrar_o_actualizar_nota(a_id, e2_id, valor=v2, estado='registrada', db_path=db_path)

    # 6. Crear Sesiones de Asistencia
    fechas_asistencia = ["2026-09-01", "2026-09-08", "2026-09-15", "2026-09-22", "2026-09-29"]
    for fecha in fechas_asistencia:
        s_id, _ = obtener_o_crear_sesion(c1_id, fecha=fecha, hora_inicio="08:00", db_path=db_path)
        for idx, a_id in enumerate(alumnos_ids):
            if idx == 0 and fecha in ["2026-09-08", "2026-09-15", "2026-09-22"]:
                registrar_asistencia_individual(s_id, a_id, estado='falta', auto_calcular_tardanza=False, db_path=db_path)
            elif idx % 5 == 0:
                registrar_asistencia_individual(s_id, a_id, estado='tardanza', hora_llegada="08:14:00", auto_calcular_tardanza=False, db_path=db_path)
            else:
                registrar_asistencia_individual(s_id, a_id, estado='presente', hora_llegada="08:02:00", auto_calcular_tardanza=False, db_path=db_path)

        cerrar_sesion_asistencia(s_id, db_path=db_path)

    print("✅ Datos de demostración creados exitosamente!")

if __name__ == "__main__":
    poblar_datos_demostracion()
