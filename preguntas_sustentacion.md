# ❓ BANCO DE PREGUNTAS Y RESPUESTAS TÉCNICAS PARA LA SUSTENTACIÓN

Este documento contiene 25 preguntas altamente probables que el jurado o docente evaluador podría realizar durante la sustentación de **AsistDoc**, junto con la respuesta técnica exacta basada en el código real.

---

### CATEGORÍA 1: PROYECTO Y JUSTIFICACIÓN
1. **¿Por qué decidieron desarrollar un sistema local y no una aplicación web en la nube?**
   *Respuesta:* Desarrollamos un sistema local para garantizar el 100% de operatividad en aulas donde la conexión a internet es inestable o inexistente, proteger la privacidad de los datos de los estudiantes al no almacenar información sensible en servidores externos y eliminar costos de infraestructura o licencias en la nube.

2. **¿Cuál es el valor agregado diferencial de AsistDoc frente a usar simplemente Excel?**
   *Respuesta:* Excel no aplica restricciones relacionales de integridad (como evitar dos notas para la misma prueba o dos asistencias en la misma fecha), requiere fórmulas manuales complejas propensas a errores de edición y carece de un historial de auditoría auditado que registre cuándo y qué nota fue modificada ante un reclamo.

---

### CATEGORÍA 2: GESTIÓN DE PROYECTOS
3. **¿Cómo delimitaron el alcance del proyecto?**
   *Respuesta:* Definimos el alcance utilizando el enfoque de gestión individual del docente, incluyendo periodos, cursos, horarios, asistencias, notas, riesgo y exportaciones, dejando explícitamente fuera del alcance la arquitectura multi-usuario o portales web para evitar sobre-ingeniería no requerida.

4. **¿Cómo gestionaron los riesgos de corrupción de la base de datos local?**
   *Respuesta:* Implementamos transacciones relacionales atómicas mediante bloques `with sqlite3.connect()` que revierten cualquier operación ante errores, y un módulo de backups que crea copias instantáneas de la base de datos SQLite en formato `.db`.

---

### CATEGORÍA 3: ARQUITECTURA Y TECNOLOGÍA
5. **¿Por qué eligieron Python y Streamlit para la interfaz?**
   *Respuesta:* Python nos ofreció un ecosistema maduro para el procesamiento de datos (*pandas*, *openpyxl*, *ReportLab*). Streamlit nos permitió construir una interfaz reactiva rápida y modular directamente en Python sin requerir motores web pesados ni código JavaScript complejo.

6. **¿Cómo está estructurada la arquitectura del código?**
   *Respuesta:* Es una arquitectura en 3 capas desacopladas: Presentación (`app.py`), Lógica de Negocio (`cursos.py`, `alumnos.py`, `asistencia.py`, `notas.py`, `reportes.py`) y Persistencia (`database.py`, `exportaciones.py`, `backups.py`).

---

### CATEGORÍA 4: BASE DE DATOS Y SQLITE
7. **¿Por qué eligieron SQLite y cómo aseguran las claves foráneas?**
   *Respuesta:* SQLite es un motor de base de datos relacional serverless, autocontenido y altamente eficiente. Para asegurar la integridad referencial, ejecutamos explícitamente el comando `PRAGMA foreign_keys = ON;` al abrir cada conexión.

8. **¿Cómo evitaron registros duplicados de notas o asistencias?**
   *Respuesta:* Definimos restricciones únicas a nivel de esquema en SQLite, como `UNIQUE(sesion_id, alumno_id)` en la tabla `asistencias` y `UNIQUE(alumno_id, evaluacion_id)` en la tabla `notas`.

9. **¿Qué ocurre si un docente elimina un curso o retira un alumno?**
   *Respuesta:* Aplicamos eliminación lógica mediante la columna `activo = 0`. Esto preserva intacta la historia académica, las notas pasadas y el historial de asistencias sin destruir información en la base de datos.

---

### CATEGORÍA 5: LÓGICA ACADÉMICA Y NOTAS
10. **¿Cómo manejan la condición 'NP' (No Se Presentó) en los promedios?**
    *Respuesta:* En la tabla `notas`, se almacena con `valor = NULL` y `estado = 'NP'`. Al calcular el promedio ponderado, el algoritmo asigna un valor numérico equivalente a $0.0$, pero preserva la etiqueta visual 'NP' en las matrices y actas.

11. **¿Cómo funciona la calculadora '¿Cuánto Necesita?'**
    *Respuesta:* Aplica la fórmula despejada: $NotaReq = (NotaMinima - SumaActual) / (PesoPendiente / 100)$. Si la nota requerida supera la escala máxima del curso (ej. > 20), el sistema alerta que no es posible aprobar únicamente con esa evaluación.

12. **¿Cómo gestionan el redondeo de los promedios?**
    *Respuesta:* Las notas individuales no se alteran. El redondeo se aplica al promedio final según la regla configurada en el curso (por ejemplo, redondeo tradicional desde 0.5 donde 10.50 sube a 11.0 pero 10.49 se mantiene en 10.0).

13. **¿Qué pasa si la suma de pesos de las evaluaciones no llega al 100%?**
    *Respuesta:* La interfaz muestra una advertencia visual permanente indicando la suma actual (ej. 80%) y el sistema calcula los promedios parciales de forma ponderada proporcional a lo evaluado hasta la fecha.

---

### CATEGORÍA 6: ASISTENCIA Y TARDANZAS
14. **¿Cómo funciona el cálculo automático de tardanzas?**
    *Respuesta:* Comparando la hora de registro del alumno con la suma de la `hora_inicio` de la clase más los `minutos_tolerancia` definidos en el horario del curso.

15. **¿Qué sucede al presionar 'Cerrar Asistencia'?**
    *Respuesta:* La sesión pasa a estado `'cerrada'`, los alumnos sin marcas previas reciben automáticamente la condición de `'falta'` y la sesión se bloquea para evitar modificaciones no supervisadas.

---

### CATEGORÍA 7: BÚSQUEDA Y NORMALIZACIÓN
16. **¿Cómo resolvieron que la búsqueda encuentre nombres con tildes o eñes?**
    *Respuesta:* Implementamos la normalización Unicode NFKD en `utils.py`, que descompone los caracteres especiales eliminando diacríticos y convirtiendo todo a minúsculas antes de comparar.

17. **¿Cómo funciona el modo 'Ingreso Rápido' sin requerir ratón?**
    *Respuesta:* Utiliza formularios `st.form` y variables de estado `st.session_state`. Al escribir el término de búsqueda y presionar Enter, se selecciona al alumno, se ingresa la nota y al enviar se limpia el input para la siguiente entrada.

---

### CATEGORÍA 8: REPORTES Y EXPORTACIÓN
18. **¿Cómo generan los archivos Excel y qué librería utilizan?**
    *Respuesta:* Utilizamos `openpyxl`, creando hojas de trabajo con fuentes personalizadas, bordes, congelamiento de encabezados y rellenos condicionales de color verde para aprobados y rojo para desaprobados.

19. **¿Cómo generan los documentos PDF oficiales?**
    *Respuesta:* Utilizamos `ReportLab`, construyendo documentos mediante `SimpleDocTemplate`, hojas de estilo y tablas con `TableStyle` repetibles en cada página.

---

### CATEGORÍA 9: PRUEBAS Y CALIDAD
20. **¿Cómo comprobaron que el software no contenga errores?**
    *Respuesta:* Desarrollamos una suite automatizada de 28 pruebas unitarias con `pytest` que verifica la integridad SQLite, la exactitud matemática de promedios, la tardanza automática, la re-apertura de archivos exportados y el ciclo de backups.

21. **¿Qué es la prueba de idempotencia en `seed.py`?**
    *Respuesta:* Es una prueba que comprueba que ejecutar el script de datos demo una segunda vez consecutiva no corrompa la base de datos ni inserte registros duplicados.

---

### CATEGORÍA 10: LIMITACIONES Y FUTURO
22. **¿Cuál es la principal limitación actual de AsistDoc?**
    *Respuesta:* Su diseño está centrado en un único docente por máquina. Para múltiples docentes simultáneos se requeriría migrar la persistencia a un motor cliente-servidor como PostgreSQL.

23. **¿Cómo escalarían AsistDoc en el futuro?**
    *Respuesta:* Añadiendo un módulo opcional de sincronización diferida mediante archivos cifrados o una API REST para conectar con sistemas centrales cuando exista internet.

24. **¿Por qué prefirieron guardar la condición NP como NULL en lugar de colocar un texto 'NP'?**
    *Respuesta:* Para mantener la columna de valor con tipo numérico (`REAL`) en SQLite, permitiendo funciones de agregación SQL sin mezclar datos de texto y número en la misma columna.

25. **¿Qué garantiza que el sistema pueda presentarse como un proyecto de software profesional?**
    *Respuesta:* La combinación de una arquitectura modular desacoplada, diseño de base de datos normalizado, suite de pruebas automatizadas con 100% de aprobación y la generación de documentación técnica formal en LaTeX.
