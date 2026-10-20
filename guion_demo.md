# 🎬 GUION DE DEMOSTRACIÓN EN VIVO (5 MINUTOS) — ASISTDOC

Este guion le guía paso a paso durante la demostración en vivo de **AsistDoc** frente al docente o jurado.

---

### PASO 1: Inicio de AsistDoc (30 segundos)
- **Acción:** Abra su terminal y ejecute `streamlit run app.py`.
- **Qué decir:** *"Iniciamos la aplicación localmente mediante Streamlit. Como pueden observar, la interfaz abre de inmediato en nuestro navegador en el panel inicial 'Hoy'."*
- **Qué se muestra:** El Dashboard "Hoy" con la clase programada del día (*Redes II — Sección A*) e indicadores globales.

---

### PASO 2: Control de Asistencia Rápida (1 minuto)
- **Acción:** Presione el botón **"Iniciar / Ver Asistencia"** en la clase *Redes II*.
- **Qué decir:** *"Al ingresar a la sesión de hoy, el docente puede registrar a todos los estudiantes matriculados en 1 segundo presionando 'Todos presentes'."*
- **Acción:** Presione **"Todos presentes"**. Luego cambie a un alumno (ej. *Pedro Soto*) a hora 08:14.
- **Qué decir:** *"Si un estudiante llega a las 08:14 y la clase iniciaba a las 08:00 con 10 minutos de tolerancia, el sistema calcula automáticamente la condición de tardanza."*
- **Acción:** Presione **"Cerrar Asistencia"**.
- **Qué decir:** *"Al cerrar la sesión, los no registrados se marcan automáticamente como falta y la sesión queda bloqueada para evitar ediciones accidentales."*

---

### PASO 3: Ingreso Rápido de Notas (Función Estrella - 1.5 minutos)
- **Acción:** Diríjase al menú lateral **Notas** $\rightarrow$ pestaña **INGRESO RÁPIDO**.
- **Qué decir:** *"Pasamos al módulo de calificaciones. Seleccionamos la evaluación 'Práctica 2'. En el buscador escribimos 'mamani' sin tildes ni mayúsculas."*
- **Acción:** Escriba `mamani` en el buscador.
- **Qué decir:** *"El sistema selecciona automáticamente a Carlos Mamani. Escribimos la nota 15 y presionamos Enter."*
- **Acción:** Ingrese `15` y presione Enter.
- **Qué decir:** *"Aparece la confirmación '✓ Carlos Mamani — 15.0' y la pantalla queda limpia para el siguiente alumno. Si un estudiante no asistió, escribimos 'NP' y Enter."*

---

### PASO 4: Matriz de Notas y Calculadora (1 minuto)
- **Acción:** Cambie a la pestaña **Matriz de Notas**.
- **Qué decir:** *"En la matriz observamos la consolidación dinámica con colores semánticos: verde para aprobados y rojo para desaprobados."*
- **Acción:** Cambie a la pestaña **¿Cuánto Necesita?**.
- **Qué decir:** *"En la calculadora seleccionamos a un alumno con el examen final pendiente. El sistema calcula exactamente qué nota sobre 20 necesita para alcanzar la nota mínima 11.0."*

---

### PASO 5: Alumnos en Riesgo y Exportación (1 minuto)
- **Acción:** Diríjase al menú **Reportes** $\rightarrow$ pestaña **Alumnos en Riesgo**.
- **Qué decir:** *"El motor de reglas evalúa inasistencias y notas, identificando a los alumnos en 'ALTO RIESGO' e indicando el motivo exacto, por ejemplo: promedio menor a 11.0 o faltas superiores al 30%."*
- **Acción:** Presione **"Generar Acta Excel"** y **"Generar Acta PDF"**.
- **Qué decir:** *"Finalmente, con un solo clic exportamos el acta en Excel con formato condicional de colores y el acta oficial en PDF lista para ser impresa e entregada."*
