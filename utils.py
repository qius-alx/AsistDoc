import unicodedata
import logging
import os

# Configuración del Logger
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "asistdoc.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)

def get_logger():
    return logging.getLogger("asistdoc")

def normalize_text(text: str) -> str:
    """
    Normaliza un texto eliminando tildes, convirtiéndolo a minúsculas y quitando espacios extra.
    Ejemplo: 'José Pérez' -> 'jose perez'
    """
    if not text:
        return ""
    text = text.strip().lower()
    # Descomponer caracteres Unicode
    nfkd_form = unicodedata.normalize('NFKD', text)
    # Filtrar diacríticos
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def format_nota(valor, estado) -> str:
    """
    Retorna el texto formateado para la nota.
    """
    if estado == 'NP':
        return 'NP'
    if estado == 'pendiente' or valor is None:
        return '-'
    return f"{float(valor):.1f}"
