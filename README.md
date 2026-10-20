# 📚 AsistDoc — Sistema de Gestión Académica Local para Docentes

**AsistDoc** es un sistema local completo, coherente y modular diseñado para que un docente gestione sus cursos, estudiantes, asistencias, evaluaciones, calificaciones, reportes académicos y copias de seguridad sin necesidad de conexión a internet ni servidores externos.

---

## 🛠️ Requisitos del Sistema

- **Python:** 3.10 o superior (Probado en 3.12)
- **Sistema Operativo:** Windows, Linux o macOS
- **Almacenamiento Local:** Base de datos SQLite (`data/asistdoc.db`)

---

## 🚀 Guía de Instalación y Ejecución

### 1. Clonar / Descargar el proyecto

Asegúrate de estar en el directorio raíz de `AsistDoc`.

### 2. Crear entorno virtual

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (CMD / PowerShell):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Generar datos de demostración (Seed)

Ejecuta el script de inicialización para poblar la base de datos con periodos, cursos, horarios, 30 alumnos ficticios, evaluaciones, notas y asistencias listas para ser mostradas en la presentación:

```bash
python seed.py
```

### 5. Ejecutar la Aplicación

```bash
streamlit run app.py
```

---

## 🧪 Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias e integrales con `pytest` que verifican la integridad de SQLite, restricciones únicas, cálculos de promedios, tardanzas, normalización de búsquedas sin tildes, motor de riesgo y exportaciones.

Para ejecutar todas las pruebas:

```bash
python3 -m pytest tests/
```

---

## 📂 Arquitectura del Proyecto

```text
AsistDoc/
│
├── app.py                   # Interfaz de usuario Streamlit modular
├── database.py              # Gestión SQLite, esquema relacional, PRAGMA e historial
├── cursos.py                # Lógica de negocio para periodos, cursos y horarios
├── alumnos.py               # Gestión de alumnos, matrículas e importación CSV/Excel
├── asistencia.py           # Control de sesiones, marcado rápido "Todos presentes" y tardanzas
├── notas.py                 # Matriz de calificaciones, evaluaciones e Ingreso Rápido
├── reportes.py              # Motor de reglas para Alumnos en Riesgo y gráficos Plotly
├── exportaciones.py         # Generación de actas y reportes en Excel (openpyxl) y PDF (reportlab)
├── qr_utils.py              # Módulo de carnets e identificación QR
├── backups.py               # Gestión de respaldos .db y restauración segura
├── config.py                # Constantes globales del sistema
├── utils.py                 # Funciones auxiliares de normalización de texto y formateo
├── seed.py                  # Poblador de datos de demostración
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación del sistema
│
├── data/
│   └── asistdoc.db          # Base de datos SQLite local
├── backups/                 # Almacenamiento de copias de seguridad
├── exports/                 # Archivos Excel y PDF generados
└── tests/                   # Suite de pruebas automatizadas con pytest
```

---

## 🎯 Guía para la Demostración Académica (5-10 minutos)

1. **Escena 1 — Panel Hoy:** Muestra las clases programadas para el día y si la asistencia está pendiente.
2. **Escena 2 — Asistencia Rápida:** Abre un curso, inicia la asistencia, presiona `Todos presentes`, corrige tardanza/falta en 2 alumnos y cierra la sesión.
3. **Escena 3 — Ingreso Rápido de Notas (Función Principal):** Ve a `Notas` -> `Ingreso Rápido`. Selecciona una evaluación, busca `mamani` (demuestra que encuentra a "Carlos Mamani" ignorando mayúsculas y tildes), ingresa `15` y presiona `Enter`.
4. **Escena 4 — Matriz de Notas:** Visualiza la acta dinámica con promedios y condiciones actualizados en tiempo real.
5. **Escena 5 — Calculadora "¿Cuánto Necesita?":** Muestra cuánto requiere un alumno en su evaluación pendiente para aprobar.
6. **Escena 6 — Alumnos en Riesgo:** Consulta la clasificación de riesgo por rendimiento, faltas o ambos.
7. **Escena 7 — Reportes y Exportación:** Visualiza los gráficos interactivos de Plotly y genera el acta en Excel (`openpyxl`) y PDF (`reportlab`).
8. **Escena 8 — Copia de Seguridad:** Genera una copia de seguridad en `.db` desde `Configuración`.
