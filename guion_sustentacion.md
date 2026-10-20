# 🎙️ GUION DE SUSTENTACIÓN ACADÉMICA — ASISTDOC
**Duración aproximada:** 12 a 15 minutos
**Formato:** Exposición fluida y natural orientada a defender el proyecto de Ingeniería de Software e Integración de Sistemas.

---

### Diapositiva 1: Portada (30 segundos)
**Qué decir:**
"Estimado docente y miembros del jurado, tengan ustedes muy buenos días. Presento ante ustedes el proyecto **AsistDoc**, un sistema local e independiente diseñado para resolver la problemática de la gestión de asistencia y calificaciones académicas desde la perspectiva del docente universitario."

---

### Diapositiva 2: Problemática (1 minuto)
**Qué decir:**
"En la práctica docente habitual, la gestión de clases implica consumir una fracción considerable de tiempo en la toma manual de listas y el registro de notas en múltiples archivos de hojas de cálculo. Esto genera tres inconvenientes principales: la fragmentación de la información con riesgo de imprecisión en los promedios finalizados, la lentitud durante la clase lectiva y la dificultad para detectar a tiempo qué estudiantes se encuentran en riesgo de desaprobar por faltas acumuladas o bajo rendimiento."

---

### Diapositiva 3: Solución Propuesta (1 minuto)
**Qué decir:**
"Como respuesta a esta necesidad, desarrollamos **AsistDoc**, una aplicación modular que opera de manera 100% local y offline en la computadora del docente. Elegimos una arquitectura local para garantizar privacidad absoluta de los datos de los estudiantes, eliminar la dependencia de servidores en la nube o conexión a internet, y brindar una agilidad de respuesta inmediata."

---

### Diapositiva 4: Objetivos del Proyecto (1 minuto)
**Qué decir:**
"El objetivo general fue construir un sistema autónomo que centralice la gestión de asignaturas, alumnos, toma de asistencia con tardanzas automáticas, matriz de notas con pesos porcentuales y generación de reportes oficiales. Entre los objetivos específicos destacan la implementación de un esquema relacional estricto en SQLite, el desarrollo del modo de 'Ingreso Rápido de Notas' y la construcción de un motor de reglas para la clasificación de riesgo estudiantil."

---

### Diapositiva 5: Gestión del Proyecto y Alcance (1 minuto)
**Qué decir:**
"Aplicando principios de Gestión de Software, delimitamos un alcance pragmático enfocado en la labor del docente individual. El alcance incluye periodos, cursos, horarios semanales, importación masiva de alumnos, control de asistencia, notas con soporte para la condición 'No Se Presentó' (NP), calculadora de metas y exportación a Excel y PDF. Dejamos explícitamente fuera del alcance los portales multi-usuario y la sincronización remota para mantener la robustez del sistema local."

---

### Diapositiva 6: Arquitectura del Software (1 minuto)
**Qué decir:**
"La arquitectura se diseñó en tres capas desacopladas: la Capa de Presentación construida con la librería Streamlit en Python, la Capa de Lógica de Negocio organizada en módulos independientes para cursos, alumnos, asistencia, notas y reportes, y la Capa de Persistencia e Integración basada en SQLite, `openpyxl` para reportes Excel y `ReportLab` para documentos PDF oficiales."

---

### Diapositiva 7: Diseños de Base de Datos (1 minuto)
**Qué decir:**
"En la base de datos `asistdoc.db` implementamos 11 tablas relacionales. Activamos explícitamente la verificación de claves foráneas con `PRAGMA foreign_keys = ON` y establecimos restricciones de unicidad estrictas, como evitar dos registros de asistencia para el mismo alumno en la misma sesión o notas duplicadas en una evaluación. Además, incluimos 11 índices para garantizar que las búsquedas se ejecuten en milisegundos."

---

### Diapositiva 8: Asistencia y Control de Tardanzas (1 minuto)
**Qué decir:**
"El módulo de asistencia permite aperturar sesiones por fecha y hora. Incluye la función de marcado masivo 'Todos presentes' que registra a todo el grupo con un solo clic. Además, el sistema compara la hora de llegada del estudiante con la tolerancia configurada en el horario del curso; si la hora de llegada supera la tolerancia, asigna automáticamente la condición de 'tardanza'. Al cerrar la sesión, los no registrados se marcan automáticamente como falta."

---

### Diapositiva 9: Módulo de Notas — Función Estrella (1 minuto y medio)
**Qué decir:**
"Llegamos al módulo principal: el 'Ingreso Rápido de Notas'. Diseñamos un flujo optimizado donde el docente selecciona la evaluación activa y busca al estudiante. Utilizando el estándar Unicode NFKD, el buscador ignora tildes, mayúsculas y acentos diacríticos: si escribimos 'mamani', encuentra de inmediato a 'Carlos Mamani'. Al ingresar la nota y presionar 'Enter', la calificación se guarda y el formulario se limpia al instante para el siguiente alumno. Además, la condición 'NP' se almacena correctamente como valor nulo para contarse numéricamente como 0 en los promedios sin perder su etiqueta visual."

---

### Diapositiva 10: Seguimiento Académico y Riesgo (1 minuto)
**Qué decir:**
"Para apoyar la tutoría docente, implementamos dos herramientas clave: la calculadora '¿Cuánto Necesita?', que indica la calificación requerida en una prueba pendiente para alcanzar la nota mínima aprobatoria, y el Motor de Reglas de Alumnos en Riesgo, que evalúa si el estudiante posee un promedio menor a 11 o inasistencias superiores al 30%, clasificándolo automáticamente en estado NORMAL, ATENCIÓN o ALTO RIESGO."

---

### Diapositiva 11: Exportación y Reportes (1 minuto)
**Qué decir:**
"AsistDoc genera actas finales de notas en Excel utilizando `openpyxl`, aplicando estilos visuales, congelado de paneles y formato condicional en verde para aprobados y rojo para desaprobados. Asimismo, utiliza `ReportLab` para construir actas oficiales e imprimibles en PDF y Plotly para la generación de gráficos interactivos de distribución de notas."

---

### Diapositiva 12: Pruebas y Resultados de Calidad (1 minuto)
**Qué decir:**
"Para garantizar la confiabilidad, construimos una suite completa de 28 pruebas unitarias e integrales con `pytest`. Las pruebas verifican desde las restricciones relacionales de SQLite y la exactitud matemática de los promedios hasta el comportamiento de la tardanza automática, la re-apertura de archivos Excel y el ciclo de copias de seguridad. El 100% de las pruebas se ejecutó con resultado exitoso."

---

### Diapositiva 13: Demostración en Vivo (30 segundos)
**Qué decir:**
"A continuación, daré inicio a la demostración en vivo del software ejecutando la secuencia real de uso de un docente durante una sesión de clase."

---

### Diapositiva 14: Conclusiones (30 segundos)
**Qué decir:**
"En conclusión, AsistDoc demuestra que es posible construir un sistema académico ágil, privado y de alta calidad técnica que resuelve de manera integral las necesidades del docente universitario sin depender de infraestructuras complejas. Quedo a su entera disposición para responder sus preguntas. Muchas gracias."
