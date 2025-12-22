"""
Electric Tariffs App - Base de Datos SQLite
============================================
Conexión y esquema de 5 tablas según ERS sección 5.1.
Inicialización incluye admin precreado y 10 tarifas UNE.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional
import secrets

import bcrypt

from core.config import (
    DB_FULL_PATH,
    BCRYPT_ROUNDS,
    DEFAULT_ADMIN_USER,
    DEFAULT_ADMIN_PASS,
    RECOVERY_KEY_PATH,
)
from core.models import TARIFAS_UNE_DEFAULT


# =============================================================================
# ESQUEMA SQL
# =============================================================================

SCHEMA_SQL = """
-- Tabla: usuarios (ERS 5.1)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'user' CHECK(rol IN ('admin', 'user')),
    estado TEXT NOT NULL DEFAULT 'ACTIVO' CHECK(estado IN ('ACTIVO', 'INACTIVO')),
    debe_cambiar_pass INTEGER NOT NULL DEFAULT 0,
    tema_preferido TEXT NOT NULL DEFAULT 'oscuro' CHECK(tema_preferido IN ('oscuro', 'claro')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: medidores (ERS 5.1)
CREATE TABLE IF NOT EXISTS medidores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    propietario_id INTEGER NOT NULL,
    etiqueta TEXT NOT NULL,
    numero_serie TEXT,
    umbral_alerta REAL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (propietario_id) REFERENCES usuarios(id),
    UNIQUE(propietario_id, etiqueta)
);

-- Tabla: vinculaciones (ERS 5.1)
CREATE TABLE IF NOT EXISTS vinculaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    medidor_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (medidor_id) REFERENCES medidores(id),
    UNIQUE(usuario_id, medidor_id)
);

-- Tabla: tarifas (ERS 5.1)
CREATE TABLE IF NOT EXISTS tarifas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    limite_min REAL NOT NULL,
    limite_max REAL,
    precio_kwh REAL NOT NULL
);

-- Tabla: lecturas (ERS 5.1)
CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medidor_id INTEGER NOT NULL,
    autor_user_id INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    lectura_anterior REAL NOT NULL,
    lectura_actual REAL NOT NULL,
    consumo_kwh REAL NOT NULL,
    importe_total REAL NOT NULL,
    es_rollover INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (medidor_id) REFERENCES medidores(id) ON DELETE CASCADE,
    FOREIGN KEY (autor_user_id) REFERENCES usuarios(id),
    UNIQUE(medidor_id, fecha_inicio, fecha_fin)
);

-- Índices para optimizar consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_lecturas_medidor ON lecturas(medidor_id);
CREATE INDEX IF NOT EXISTS idx_lecturas_fecha ON lecturas(fecha_fin);
CREATE INDEX IF NOT EXISTS idx_medidores_propietario ON medidores(propietario_id);
CREATE INDEX IF NOT EXISTS idx_vinculaciones_usuario ON vinculaciones(usuario_id);
"""


# =============================================================================
# GESTIÓN DE CONEXIÓN
# =============================================================================

class DatabaseManager:
    """
    Gestor de conexión SQLite.
    Implementa patrón Context Manager para manejo seguro de transacciones.
    """
    
    _instance: Optional["DatabaseManager"] = None
    
    def __new__(cls) -> "DatabaseManager":
        """Singleton para asegurar una única instancia."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self._db_path = DB_FULL_PATH
        self._initialized = True
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Obtiene conexión a la base de datos.
        Row factory permite acceso por nombre de columna.
        """
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def initialize_database(self) -> None:
        """
        Inicializa la base de datos:
        1. Crea tablas si no existen
        2. Crea admin por defecto si no existe (RF-01)
        3. Carga tarifas UNE si tabla vacía (RF-03)
        4. Genera recovery_key.txt si no existe (RF-04)
        """
        with self.get_connection() as conn:
            # Crear esquema
            conn.executescript(SCHEMA_SQL)
            
            # Verificar si admin existe
            cursor = conn.execute(
                "SELECT id FROM usuarios WHERE username = ?",
                (DEFAULT_ADMIN_USER,)
            )
            if cursor.fetchone() is None:
                self._create_default_admin(conn)
            
            # Verificar si hay tarifas
            cursor = conn.execute("SELECT COUNT(*) FROM tarifas")
            if cursor.fetchone()[0] == 0:
                self._load_default_tarifas(conn)
            
            # Generar recovery key si no existe
            self._ensure_recovery_key()
            
            conn.commit()
    
    def _create_default_admin(self, conn: sqlite3.Connection) -> None:
        """
        Crea usuario admin por defecto (RF-01).
        debe_cambiar_pass=1 para forzar cambio en primer login (RF-02).
        """
        password_hash = bcrypt.hashpw(
            DEFAULT_ADMIN_PASS.encode("utf-8"),
            bcrypt.gensalt(BCRYPT_ROUNDS)
        ).decode("utf-8")
        
        conn.execute(
            """
            INSERT INTO usuarios (nombre, username, password_hash, rol, debe_cambiar_pass)
            VALUES (?, ?, ?, 'admin', 1)
            """,
            ("Administrador", DEFAULT_ADMIN_USER, password_hash)
        )
    
    def _load_default_tarifas(self, conn: sqlite3.Connection) -> None:
        """Carga las 10 tarifas UNE precargadas (RF-03, ERS 5.2)."""
        for tarifa in TARIFAS_UNE_DEFAULT:
            conn.execute(
                """
                INSERT INTO tarifas (limite_min, limite_max, precio_kwh)
                VALUES (?, ?, ?)
                """,
                (tarifa["limite_min"], tarifa["limite_max"], tarifa["precio_kwh"])
            )
    
    def _ensure_recovery_key(self) -> None:
        """
        Genera archivo recovery_key.txt con clave maestra (RF-04).
        Solo se crea si no existe.
        """
        if not RECOVERY_KEY_PATH.exists():
            recovery_key = secrets.token_urlsafe(32)
            RECOVERY_KEY_PATH.write_text(
                f"CLAVE DE RECUPERACIÓN - Electric Tariffs App\n"
                f"=============================================\n"
                f"Generada: {datetime.now().isoformat()}\n\n"
                f"CLAVE: {recovery_key}\n\n"
                f"IMPORTANTE: Guarda este archivo en un lugar seguro.\n"
                f"Esta clave permite resetear la contraseña del administrador.\n"
            )
            # Intentar hacer el archivo solo lectura (best effort)
            try:
                RECOVERY_KEY_PATH.chmod(0o400)
            except OSError:
                pass  # En Windows puede no funcionar


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_db() -> DatabaseManager:
    """Obtiene instancia del gestor de base de datos."""
    return DatabaseManager()


def init_db() -> None:
    """
    Inicializa la base de datos.
    DEBE llamarse en main.py antes de cargar cualquier UI.
    """
    db = get_db()
    db.initialize_database()
