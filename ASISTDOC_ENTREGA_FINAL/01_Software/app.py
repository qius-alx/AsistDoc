import streamlit as st
import pandas as pd
from datetime import datetime

from database import init_db, obtener_historial_reciente
from cursos import (
    listar_periodos, crear_periodo, cambiar_estado_periodo,
    listar_cursos, crear_curso, actualizar_curso, cambiar_estado_curso,
    obtener_clases_del_dia, agregar_horario, listar_horarios_curso
)
from alumnos import (
    listar_alumnos_curso, buscar_alumnos_en_curso, crear_o_obtener_alumno,
    matricular_alumno, retirar_alumno_de_curso, importar_alumnos_df
)
from asistencia import (
    obtener_o_crear_sesion, marcar_todos_presentes, registrar_asistencia_individual,
    cerrar_sesion_asistencia, abrir_sesion_para_correccion, obtener_resumen_asistencia_sesion
)
from notas import (
    listar_evaluaciones_curso, crear_evaluacion, actualizar_evaluacion,
    verificar_suma_pesos, registrar_o_actualizar_nota, deshacer_ultimo_ingreso_nota,
    calcular_promedio_alumno, calcular_nota_necesaria, obtener_matriz_notas_curso
)
from reportes import (
    analizar_alumnos_en_riesgo, obtener_estadisticas_generales_curso,
    generar_grafico_distribucion_notas, generar_grafico_resumen_asistencia
)
from exportaciones import (
    exportar_acta_notas_excel, exportar_reporte_riesgo_excel, exportar_acta_notas_pdf
)
from qr_utils import (
    generar_codigo_qr_bytes, generar_carnet_alumno, decodificar_qr_texto
)
from backups import (
    crear_backup_base_datos, listar_backups_disponibles, restaurar_backup_base_datos
)
from utils import normalize_text, format_nota

# Inicializar Base de Datos
init_db()

# Configuración de Página
st.set_page_config(
    page_title="AsistDoc - Gestión Académica Local",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Limpios
st.markdown("""
<style>
    .stApp { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .metric-card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 4px solid #1f77b4; }
    .status-badge-presente { background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .status-badge-tardanza { background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .status-badge-falta { background-color: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Navegación Principal
st.sidebar.title("📚 AsistDoc")
st.sidebar.caption("Sistema Local para Gestión Docente")

modulo = st.sidebar.radio(
    "Menú Principal",
    ["Hoy", "Cursos y alumnos", "Asistencia", "Notas", "Reportes", "Configuración"]
)

st.sidebar.markdown("---")
periodos_activos = listar_periodos(solo_activos=True)
if periodos_activos:
    periodo_sel = st.sidebar.selectbox("Periodo Activo", [p['nombre'] for p in periodos_activos])
    periodo_actual_id = next(p['id'] for p in periodos_activos if p['nombre'] == periodo_sel)
else:
    st.sidebar.warning("⚠️ No hay periodos activos. Cree uno en Configuración.")
    periodo_actual_id = None

# ==========================================
# 1. PANEL "HOY"
# ==========================================
if modulo == "Hoy":
    st.title("📌 Dashboard — Clases del Día")
    st.markdown("Identifica automáticamente las clases programadas para el día de hoy y el estado de la asistencia.")

    if not periodo_actual_id:
        st.info("Cree un periodo lectivo para comenzar.")
    else:
        clases_hoy = obtener_clases_del_dia()
        if not clases_hoy:
            st.info("☕ No hay clases programadas para el día de hoy según los horarios definidos.")
        else:
            st.subheader(f"📅 Clases Programadas para Hoy ({datetime.now().strftime('%A %d/%m/%Y')})")
            cols = st.columns(len(clases_hoy) if len(clases_hoy) <= 3 else 3)
            for idx, clase in enumerate(clases_hoy):
                col = cols[idx % 3]
                with col:
                    st.markdown(f"### {clase['curso_nombre']} ({clase['seccion']})")
                    st.write(f"⏰ **Horario:** {clase['hora_inicio']} - {clase['hora_fin']}")
                    est_sesion = clase['sesion_estado'] or 'Pendiente'
                    if est_sesion == 'abierta':
                        st.warning("🟡 Asistencia Abierta")
                    elif est_sesion == 'cerrada':
                        st.success("🟢 Asistencia Completada")
                    else:
                        st.error("🔴 Asistencia Pendiente")

                    if st.button(f"Iniciar / Ver Asistencia #{clase['curso_id']}", key=f"btn_hoy_{clase['curso_id']}"):
                        st.session_state['curso_asist_id'] = clase['curso_id']
                        st.rerun()

        st.markdown("---")
        # Indicadores Globales del Periodo
        cursos_p = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cursos Activos", len(cursos_p))

        tot_alumnos = sum(len(listar_alumnos_curso(c['id'])) for c in cursos_p)
        c2.metric("Alumnos Matriculados", tot_alumnos)

        tot_riesgo = sum(obtener_estadisticas_generales_curso(c['id'])['alumnos_en_riesgo'] for c in cursos_p)
        c3.metric("Alumnos en Riesgo", tot_riesgo, delta_color="inverse")

        st.metric_container = c4.metric("Sistema 100% Local", "SQLite Activo")

# ==========================================
# 2. CURSOS Y ALUMNOS
# ==========================================
elif modulo == "Cursos y alumnos":
    st.title("📘 Cursos, Horarios y Alumnos")
    tabs = st.tabs(["Cursos y Horarios", "Gestión de Alumnos", "Importación Masiva (CSV/Excel)"])

    with tabs[0]:
        st.subheader("Gestión de Cursos del Periodo")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("#### Crear Nuevo Curso")
            with st.form("form_crear_curso"):
                nom_c = st.text_input("Nombre del Curso (ej. Redes II)")
                sec_c = st.text_input("Sección (ej. A)")
                n_min = st.number_input("Nota Mínima Aprobatoria", value=11.0, min_value=0.0, max_value=20.0)
                e_max = st.number_input("Escala Máxima", value=20.0, min_value=1.0, max_value=20.0)
                lim_f = st.number_input("Límite Faltas (%)", value=30.0, min_value=0.0, max_value=100.0)
                submitted = st.form_submit_button("Guardar Curso")
                if submitted and nom_c and sec_c and periodo_actual_id:
                    try:
                        crear_curso(periodo_actual_id, nom_c, sec_c, nota_minima=n_min, escala_max=e_max, limite_faltas_pct=lim_f)
                        st.success(f"Curso {nom_c} - {sec_c} creado correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear curso: {e}")

        with col2:
            st.markdown("#### Cursos Registrados")
            cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
            if not cursos:
                st.info("No hay cursos creados en este periodo.")
            else:
                for c in cursos:
                    with st.expander(f"📘 {c['nombre']} — Sección {c['seccion']}"):
                        st.write(f"**Nota Mínima:** {c['nota_minima']} | **Escala:** {c['escala_max']} | **Límite Faltas:** {c['limite_faltas_pct']}%")
                        # Horarios del curso
                        horarios = listar_horarios_curso(c['id'])
                        dias_map = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"}
                        if horarios:
                            st.write("**Horarios:** " + ", ".join([f"{dias_map[h['dia_semana']]} {h['hora_inicio']}-{h['hora_fin']}" for h in horarios]))

                        # Agregar horario rápido
                        with st.form(f"form_horario_{c['id']}"):
                            d_idx = st.selectbox("Día", options=list(dias_map.keys()), format_func=lambda x: dias_map[x], key=f"d_{c['id']}")
                            h_ini = st.time_input("Hora Inicio", value=datetime.strptime("08:00", "%H:%M").time(), key=f"hi_{c['id']}")
                            h_fin = st.time_input("Hora Fin", value=datetime.strptime("10:00", "%H:%M").time(), key=f"hf_{c['id']}")
                            if st.form_submit_button("Agregar Horario"):
                                agregar_horario(c['id'], d_idx, h_ini.strftime("%H:%M"), h_fin.strftime("%H:%M"))
                                st.success("Horario agregado.")
                                st.rerun()

    with tabs[1]:
        st.subheader("Matrícula de Alumnos")
        cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
        if cursos:
            curso_sel_id = st.selectbox("Seleccionar Curso para ver Alumnos", [c['id'] for c in cursos], format_func=lambda x: next(f"{c['nombre']} - {c['seccion']}" for c in cursos if c['id'] == x))

            col_a1, col_a2 = st.columns([1, 2])
            with col_a1:
                st.markdown("#### Registrar Alumno Individual")
                with st.form("form_nuevo_alumno"):
                    cod_a = st.text_input("Código de Alumno")
                    nom_a = st.text_input("Nombre Completo")
                    if st.form_submit_button("Matricular Alumno") and cod_a and nom_a:
                        a_id, _ = crear_o_obtener_alumno(cod_a, nom_a)
                        matricular_alumno(a_id, curso_sel_id)
                        st.success(f"Alumno {nom_a} matriculado.")
                        st.rerun()

            with col_a2:
                st.markdown("#### Lista de Matriculados")
                alumnos_c = listar_alumnos_curso(curso_sel_id)
                if alumnos_c:
                    df_a = pd.DataFrame([{"Código": a['codigo'], "Nombre": a['nombre'], "Fecha Matrícula": a['fecha_matricula']} for a in alumnos_c])
                    st.dataframe(df_a, use_container_width=True)
                else:
                    st.info("Sin alumnos matriculados en este curso.")

    with tabs[2]:
        st.subheader("Importación Masiva desde CSV / Excel")
        cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
        if cursos:
            c_imp_id = st.selectbox("Seleccionar Curso Destino", [c['id'] for c in cursos], format_func=lambda x: next(f"{c['nombre']} - {c['seccion']}" for c in cursos if c['id'] == x), key="c_imp")
            archivo = st.file_uploader("Cargar archivo Excel o CSV (columnas requeridas: 'codigo', 'nombre')", type=["csv", "xlsx"])
            if archivo:
                try:
                    if archivo.name.endswith('.csv'):
                        df_imp = pd.read_csv(archivo)
                    else:
                        df_imp = pd.read_excel(archivo)

                    st.markdown("##### Vista Previa de Datos a Importar")
                    st.dataframe(df_imp.head(), use_container_width=True)

                    if st.button("Confirmar Importación Masiva"):
                        res = importar_alumnos_df(df_imp, c_imp_id)
                        st.success(f"Importación completada: {res['exitosos']} exitosos, {res['duplicados_curso']} ya existían, {res['invalidos']} inválidos.")
                        if res['errores']:
                            st.warning("Detalles de filas ignoradas:\n" + "\n".join(res['errores']))
                except Exception as e:
                    st.error(f"Error al leer archivo: {e}")

# ==========================================
# 3. ASISTENCIA
# ==========================================
elif modulo == "Asistencia":
    st.title("📋 Registro y Control de Asistencia")
    cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
    if not cursos:
        st.info("No hay cursos disponibles.")
    else:
        # Recuperar curso seleccionado si viene del panel Hoy
        default_idx = 0
        if 'curso_asist_id' in st.session_state:
            for idx, c in enumerate(cursos):
                if c['id'] == st.session_state['curso_asist_id']:
                    default_idx = idx
                    break

        curso_sel = st.selectbox("Seleccionar Curso", cursos, index=default_idx, format_func=lambda c: f"{c['nombre']} - {c['seccion']}")
        curso_id = curso_sel['id']

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_asist = st.date_input("Fecha de Sesión", value=datetime.now())
        with col_f2:
            hora_ini_asist = st.time_input("Hora de Inicio", value=datetime.now().time())

        fecha_str = fecha_asist.strftime("%Y-%m-%d")
        hora_str = hora_ini_asist.strftime("%H:%M")

        sesion_id, estado_sesion = obtener_o_crear_sesion(curso_id, fecha=fecha_str, hora_inicio=hora_str)

        st.markdown(f"### Sesión del {fecha_str} — Estado: **{estado_sesion.upper()}**")

        if estado_sesion == 'abierta':
            c_btn1, c_btn2, c_btn3 = st.columns(3)
            with c_btn1:
                if st.button("⚡ Marcar Todos Presentes"):
                    marcar_todos_presentes(sesion_id)
                    st.success("Todos los alumnos marcados como presentes.")
                    st.rerun()

            with c_btn2:
                if st.button("🔒 Cerrar Asistencia"):
                    resumen_c = cerrar_sesion_asistencia(sesion_id, marcar_sin_registro_como_falta=True)
                    st.success(f"Sesión cerrada. Resumen: {resumen_c}")
                    st.rerun()

        else:
            if st.button("🔓 Reabrir Sesión para Corrección"):
                abrir_sesion_para_correccion(sesion_id)
                st.success("Sesión reabierta.")
                st.rerun()

        st.markdown("---")
        resumen_alumnos = obtener_resumen_asistencia_sesion(sesion_id)
        if not resumen_alumnos:
            st.warning("No hay alumnos matriculados en este curso.")
        else:
            st.subheader("Lista de Asistencia")
            for a in resumen_alumnos:
                col_c1, col_c2, col_c3, col_c4 = st.columns([1, 3, 2, 2])
                with col_c1:
                    st.write(f"**{a['codigo']}**")
                with col_c2:
                    st.write(a['nombre'])
                with col_c3:
                    est_actual = a['estado'] or 'falta'
                    if estado_sesion == 'abierta':
                        nuevo_est = st.selectbox(
                            "Estado",
                            ["presente", "tardanza", "falta", "justificada"],
                            index=["presente", "tardanza", "falta", "justificada"].index(est_actual),
                            key=f"asist_{a['alumno_id']}_{sesion_id}"
                        )
                        if nuevo_est != est_actual:
                            registrar_asistencia_individual(sesion_id, a['alumno_id'], estado=nuevo_est)
                            st.rerun()
                    else:
                        st.write(f"**{est_actual.upper()}**")
                with col_c4:
                    st.caption(f"Llegada: {a['hora_llegada'] or '-'}")

# ==========================================
# 4. NOTAS (MÓDULO PRINCIPAL)
# ==========================================
elif modulo == "Notas":
    st.title("📝 Módulo de Evaluaciones y Calificaciones")
    cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
    if not cursos:
        st.info("No hay cursos disponibles.")
    else:
        curso_sel = st.selectbox("Seleccionar Curso", cursos, format_func=lambda c: f"{c['nombre']} - {c['seccion']}")
        curso_id = curso_sel['id']

        tabs_notas = st.tabs(["⚡ INGRESO RÁPIDO", "📊 Matriz de Notas", "⚙️ Configurar Evaluaciones", "🎯 ¿Cuánto Necesita?"])

        # TAB 1: INGRESO RÁPIDO DE NOTAS
        with tabs_notas[0]:
            st.subheader("⚡ Modo de Ingreso Rápido de Calificaciones")
            evals = listar_evaluaciones_curso(curso_id, solo_activas=True)
            if not evals:
                st.warning("Debe configurar al menos una evaluación activa para ingresar notas.")
            else:
                eval_sel = st.selectbox("1. Selección de Evaluación Activa", evals, format_func=lambda e: f"{e['nombre']} (Peso: {e['peso']}%)")
                eval_id = eval_sel['id']

                col_ir1, col_ir2 = st.columns([1, 1])

                with col_ir1:
                    st.markdown("#### Búsqueda de Alumno")
                    search_query = st.text_input("Buscar alumno (Código o Nombre)", key="search_query_ir")

                    coincidencias = buscar_alumnos_en_curso(curso_id, search_query)
                    alumno_seleccionado = None

                    if search_query.strip():
                        if not coincidencias:
                            st.error("No se encontraron coincidencias.")
                        elif len(coincidencias) == 1:
                            alumno_seleccionado = coincidencias[0]
                            st.success(f"Alumno seleccionado automáticamente: **{alumno_seleccionado['nombre']}** ({alumno_seleccionado['codigo']})")
                        else:
                            st.info(f"Se encontraron {len(coincidencias)} alumnos. Seleccione uno:")
                            opciones = {f"{a['codigo']} - {a['nombre']}": a for a in coincidencias}
                            sel_key = st.radio("Coincidencias", list(opciones.keys()))
                            alumno_seleccionado = opciones[sel_key]
                    else:
                        st.info("Ingrese un término de búsqueda arriba para seleccionar estudiante.")

                with col_ir2:
                    st.markdown("#### Formulario de Calificación")
                    if alumno_seleccionado:
                        st.info(f"👤 **Alumno:** {alumno_seleccionado['nombre']}\n\n🆔 **Código:** {alumno_seleccionado['codigo']}")

                        with st.form("form_ingreso_nota_rapido"):
                            input_nota = st.text_input("Nota (0.0 a 20.0) o escribir 'NP'", key="input_nota_rapida")
                            btn_guardar = st.form_submit_button("💾 Guardar Nota (Enter)")

                            if btn_guardar:
                                val_clean = input_nota.strip().upper()
                                try:
                                    if val_clean == "NP":
                                        registrar_o_actualizar_nota(alumno_seleccionado['id'], eval_id, valor=None, estado='NP')
                                        st.session_state['msg_exito'] = f"✓ {alumno_seleccionado['nombre']} — NP registrado"
                                    else:
                                        val_num = float(val_clean)
                                        registrar_o_actualizar_nota(alumno_seleccionado['id'], eval_id, valor=val_num, estado='registrada')
                                        st.session_state['msg_exito'] = f"✓ {alumno_seleccionado['nombre']} — {val_num:.1f}"

                                    st.rerun()
                                except ValueError as ve:
                                    st.error(f"Error de validación: {ve}")

                    if 'msg_exito' in st.session_state:
                        st.success(st.session_state['msg_exito'])

                    if st.button("↩️ Deshacer Último Ingreso"):
                        if deshacer_ultimo_ingreso_nota(curso_id):
                            st.success("Último ingreso revertido exitosamente.")
                            st.rerun()
                        else:
                            st.warning("No hay operaciones de notas recientes para deshacer.")

        # TAB 2: MATRIZ DE NOTAS
        with tabs_notas[1]:
            st.subheader("Matriz Dinámica de Calificaciones")
            df_matriz = obtener_matriz_notas_curso(curso_id)
            st.dataframe(df_matriz, use_container_width=True)

        # TAB 3: CONFIGURAR EVALUACIONES
        with tabs_notas[2]:
            st.subheader("Evaluaciones del Curso")
            suma_p, es_100 = verificar_suma_pesos(curso_id)
            if not es_100:
                st.warning(f"⚠️ La suma actual de pesos de evaluaciones activas es **{suma_p}%**. Debe sumar exactamente 100%.")
            else:
                st.success("✅ La suma de pesos es igual a 100%.")

            col_ev1, col_ev2 = st.columns([1, 2])
            with col_ev1:
                st.markdown("#### Crear Evaluación")
                with st.form("form_crear_eval"):
                    nom_e = st.text_input("Nombre (ej. Práctica 3)")
                    peso_e = st.number_input("Peso (%)", min_value=1.0, max_value=100.0, value=20.0)
                    if st.form_submit_button("Guardar Evaluación") and nom_e:
                        try:
                            crear_evaluacion(curso_id, nom_e, peso_e)
                            st.success("Evaluación creada.")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error: {ex}")

            with col_ev2:
                evals_exist = listar_evaluaciones_curso(curso_id, solo_activas=True)
                if evals_exist:
                    df_ev = pd.DataFrame([{"ID": e['id'], "Evaluación": e['nombre'], "Peso (%)": e['peso']} for e in evals_exist])
                    st.dataframe(df_ev, use_container_width=True)

        # TAB 4: ¿CUÁNTO NECESITA?
        with tabs_notas[3]:
            st.subheader("Calculadora: ¿Cuánto Necesita en Evaluación Pendiente?")
            alumnos_c = listar_alumnos_curso(curso_id)
            evals_c = listar_evaluaciones_curso(curso_id, solo_activas=True)
            if alumnos_c and evals_c:
                a_calc_id = st.selectbox("Seleccionar Alumno", [a['id'] for a in alumnos_c], format_func=lambda x: next(a['nombre'] for a in alumnos_c if a['id'] == x))
                e_calc_id = st.selectbox("Seleccionar Evaluación Pendiente Target", [e['id'] for e in evals_c], format_func=lambda x: next(f"{e['nombre']} ({e['peso']}%)" for e in evals_c if e['id'] == x))

                if st.button("Calcular Nota Requerida"):
                    res_calc = calcular_nota_necesaria(a_calc_id, curso_id, e_calc_id)
                    if res_calc['alcanzable']:
                        st.success(res_calc['mensaje'])
                    else:
                        st.error(res_calc['mensaje'])

# ==========================================
# 5. REPORTES
# ==========================================
elif modulo == "Reportes":
    st.title("📊 Reportes y Alumnos en Riesgo")
    cursos = listar_cursos(periodo_id=periodo_actual_id, solo_activos=True)
    if not cursos:
        st.info("No hay cursos disponibles.")
    else:
        curso_sel = st.selectbox("Seleccionar Curso", cursos, format_func=lambda c: f"{c['nombre']} - {c['seccion']}")
        curso_id = curso_sel['id']

        tabs_rep = st.tabs(["⚠️ Alumnos en Riesgo", "📈 Gráficos e Indicadores", "📥 Exportar Informes"])

        with tabs_rep[0]:
            st.subheader("Clasificación de Alumnos en Riesgo (Reglas Académicas)")
            st.caption("Falta Excesiva (>=30%) o Promedio Desaprobado (<11.0)")

            riesgo_data = analizar_alumnos_en_riesgo(curso_id)
            df_r = pd.DataFrame(riesgo_data)
            st.dataframe(df_r[["codigo", "nombre", "promedio", "pct_faltas", "nivel_riesgo", "motivos"]], use_container_width=True)

        with tabs_rep[1]:
            st.subheader("Estadísticas Visuales con Plotly")
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                fig1 = generar_grafico_distribucion_notas(curso_id)
                st.plotly_chart(fig1, use_container_width=True)
            with col_g2:
                fig2 = generar_grafico_resumen_asistencia(curso_id)
                st.plotly_chart(fig2, use_container_width=True)

        with tabs_rep[2]:
            st.subheader("Descargar Actas y Reportes")
            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                if st.button("📊 Generar Acta Excel"):
                    path_e = exportar_acta_notas_excel(curso_id)
                    st.success(f"Generado: {path_e}")
            with col_d2:
                if st.button("⚠️ Generar Reporte Riesgo Excel"):
                    path_r = exportar_reporte_riesgo_excel(curso_id)
                    st.success(f"Generado: {path_r}")
            with col_d3:
                if st.button("📄 Generar Acta PDF Oficial"):
                    path_p = exportar_acta_notas_pdf(curso_id)
                    st.success(f"Generado: {path_p}")

# ==========================================
# 6. CONFIGURACIÓN Y UTILIDADES
# ==========================================
elif modulo == "Configuración":
    st.title("⚙️ Configuración, Auditoría y Backups")
    tabs_conf = st.tabs(["💾 Copias de Seguridad (Backups)", "📜 Historial de Auditoría", "📅 Gestión de Periodos"])

    with tabs_conf[0]:
        st.subheader("Respaldos de Base de Datos SQLite")
        if st.button("📦 Crear Copia de Seguridad Ahora"):
            b_path = crear_backup_base_datos()
            st.success(f"Backup creado exitosamente: `{b_path}`")

        st.markdown("#### Backups Disponibles para Restauración")
        backups = listar_backups_disponibles()
        if not backups:
            st.info("No hay copias de seguridad guardadas.")
        else:
            b_sel = st.selectbox("Seleccionar Respaldo", backups)
            if st.button("⚠️ Restaurar Copia de Seguridad Seleccionada"):
                restaurar_backup_base_datos(b_sel)
                st.success("Base de datos restaurada correctamente.")
                st.rerun()

    with tabs_conf[1]:
        st.subheader("Historial Auditado de Modificaciones")
        hist = obtener_historial_reciente(50)
        if hist:
            df_h = pd.DataFrame([dict(r) for r in hist])
            st.dataframe(df_h, use_container_width=True)
        else:
            st.info("Sin registros de auditoría aún.")

    with tabs_conf[2]:
        st.subheader("Crear y Administrar Periodos Académicos")
        with st.form("form_periodo"):
            nom_p = st.text_input("Nombre de Periodo (ej. 2026-II)")
            f_ini = st.date_input("Fecha Inicio")
            f_fin = st.date_input("Fecha Fin")
            if st.form_submit_button("Crear Periodo") and nom_p:
                try:
                    crear_periodo(nom_p, f_ini.strftime("%Y-%m-%d"), f_fin.strftime("%Y-%m-%d"))
                    st.success("Periodo creado.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")
