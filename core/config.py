"""
Electric Tariffs App - Configuración Centralizada
==================================================
Carga variables desde .env y las expone como constantes tipadas.
El resto de la app importa desde aquí, NUNCA usa os.getenv directamente.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
_ROOT_DIR = Path(__file__).parent.parent
_ENV_PATH = _ROOT_DIR / ".env"
load_dotenv(_ENV_PATH)

# =============================================================================
# BASE DE DATOS
# =============================================================================
DB_PATH: str = os.getenv("DB_PATH", "app_database.db")
DB_FULL_PATH: Path = _ROOT_DIR / DB_PATH

# =============================================================================
# LOGS
# =============================================================================
LOG_PATH: str = os.getenv("LOG_PATH", "logs_actividad.csv")
LOG_FULL_PATH: Path = _ROOT_DIR / LOG_PATH

# =============================================================================
# SEGURIDAD
# =============================================================================
BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", "12"))
SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "3"))
MAX_LOGIN_ATTEMPTS: int = 3
LOCKOUT_MINUTES: int = 1

# =============================================================================
# CONFIGURACIÓN DE MEDIDOR
# =============================================================================
MAX_MEDIDOR: float = float(os.getenv("MAX_MEDIDOR", "99999.9"))
UMBRAL_ROLLOVER: float = float(os.getenv("UMBRAL_ROLLOVER", "0.95"))

# =============================================================================
# ADMIN POR DEFECTO
# =============================================================================
DEFAULT_ADMIN_USER: str = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASS: str = os.getenv("DEFAULT_ADMIN_PASS", "admin123")

# =============================================================================
# RECOVERY KEY
# =============================================================================
RECOVERY_KEY_FILE: str = os.getenv("RECOVERY_KEY_FILE", "recovery_key.txt")
RECOVERY_KEY_PATH: Path = _ROOT_DIR / RECOVERY_KEY_FILE

# =============================================================================
# UI - Estilos (RNF-01)
# =============================================================================
PRIMARY_COLOR: str = "#219cba"
BORDER_RADIUS: int = 15
FONT_FAMILY: str = "Inter"

# =============================================================================
# VALIDACIONES
# =============================================================================
MIN_PASSWORD_LENGTH: int = 6
VINCULADO_EDIT_HOURS: int = 48
HISTORY_YEARS: int = 5
