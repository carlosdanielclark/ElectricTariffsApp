"""
Electric Tariffs App - Modelos del Dominio
==========================================
Entidades definidas como dataclasses con tipado estricto.
NUNCA importar flet o sqlite3 aquí.
Usar 'rol' (español) en lugar de 'role' según agent.md.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


# =============================================================================
# ENUMERACIONES
# =============================================================================

class RolUsuario(str, Enum):
    """Roles de usuario según ERS sección 2.3."""
    ADMIN = "admin"
    USER = "user"


class EstadoUsuario(str, Enum):
    """Estados posibles de un usuario."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class TemaPreferido(str, Enum):
    """Tema visual preferido."""
    OSCURO = "oscuro"
    CLARO = "claro"


class TipoEvento(str, Enum):
    """Eventos para auditoría según RF-67."""
    LOGIN = "Login"
    LOGIN_FALLIDO = "LoginFallido"
    LOGOUT = "Logout"
    LECTURA_CREADA = "LecturaCreada"
    LECTURA_EDITADA = "LecturaEditada"
    LECTURA_ELIMINADA = "LecturaEliminada"
    ROLLOVER_DETECTADO = "RolloverDetectado"
    TARIFA_MODIFICADA = "TarifaModificada"
    USUARIO_CREADO = "UsuarioCreado"
    USUARIO_DESACTIVADO = "UsuarioDesactivado"
    USUARIO_TRANSFERIDO = "UsuarioTransferido"
    BACKUP_CREADO = "BackupCreado"
    BACKUP_RESTAURADO = "BackupRestaurado"
    MEDIDOR_CREADO = "MedidorCreado"
    MEDIDOR_ELIMINADO = "MedidorEliminado"
    VINCULACION_CREADA = "VinculacionCreada"
    VINCULACION_ELIMINADA = "VinculacionEliminada"
    PASSWORD_CAMBIADO = "PasswordCambiado"
    PASSWORD_RESETEADO = "PasswordReseteado"


# =============================================================================
# ENTIDADES
# =============================================================================

@dataclass
class Usuario:
    """
    Entidad Usuario según ERS sección 5.1.
    Usa 'rol' (español) según agent.md.
    """
    id: Optional[int] = None
    nombre: str = ""
    username: str = ""
    password_hash: str = ""
    rol: RolUsuario = RolUsuario.USER
    estado: EstadoUsuario = EstadoUsuario.ACTIVO
    debe_cambiar_pass: bool = False
    tema_preferido: TemaPreferido = TemaPreferido.OSCURO
    created_at: Optional[datetime] = None
    
    @property
    def es_admin(self) -> bool:
        """Verifica si el usuario es administrador."""
        return self.rol == RolUsuario.ADMIN
    
    @property
    def esta_activo(self) -> bool:
        """Verifica si el usuario está activo."""
        return self.estado == EstadoUsuario.ACTIVO


@dataclass
class Medidor:
    """
    Entidad Medidor según ERS sección 5.1.
    Etiqueta obligatoria, número de serie opcional.
    """
    id: Optional[int] = None
    propietario_id: int = 0
    etiqueta: str = ""
    numero_serie: Optional[str] = None
    umbral_alerta: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validar que etiqueta no esté vacía."""
        if not self.etiqueta.strip():
            raise ValueError("La etiqueta del medidor es obligatoria")


@dataclass
class Vinculacion:
    """
    Entidad Vinculación según ERS sección 5.1.
    Asocia usuario a medidor ajeno para trabajo colaborativo.
    """
    id: Optional[int] = None
    usuario_id: int = 0
    medidor_id: int = 0
    created_at: Optional[datetime] = None


@dataclass
class Tarifa:
    """
    Entidad Tarifa (tramo) según ERS sección 5.1.
    limite_max puede ser None para el último tramo (infinito).
    """
    id: Optional[int] = None
    limite_min: float = 0.0
    limite_max: Optional[float] = None
    precio_kwh: float = 0.0
    
    @property
    def es_ultimo_tramo(self) -> bool:
        """Verifica si es el tramo infinito (>500 kWh)."""
        return self.limite_max is None
    
    @property
    def rango(self) -> Optional[float]:
        """Calcula el rango del tramo. None si es infinito."""
        if self.limite_max is None:
            return None
        return self.limite_max - self.limite_min


@dataclass
class Lectura:
    """
    Entidad Lectura según ERS sección 5.1.
    Registra consumo eléctrico con soporte para rollover.
    """
    id: Optional[int] = None
    medidor_id: int = 0
    autor_user_id: int = 0
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    lectura_anterior: float = 0.0
    lectura_actual: float = 0.0
    consumo_kwh: float = 0.0
    importe_total: float = 0.0
    es_rollover: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def importe_redondeado(self) -> int:
        """Importe en CUP enteros para presentación (RF-39)."""
        return round(self.importe_total)
    
    @property
    def periodo_str(self) -> str:
        """Representación del período como string."""
        if self.fecha_inicio and self.fecha_fin:
            return f"{self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"
        return ""


@dataclass
class EventoLog:
    """
    Registro de evento para auditoría según RF-66/RF-67.
    Se guarda en logs_actividad.csv.
    """
    timestamp: datetime = field(default_factory=datetime.now)
    usuario_id: Optional[int] = None
    evento: TipoEvento = TipoEvento.LOGIN
    detalles: str = ""
    
    def to_csv_row(self) -> list[str]:
        """Convierte a fila CSV."""
        return [
            self.timestamp.isoformat(),
            str(self.usuario_id) if self.usuario_id else "",
            self.evento.value,
            self.detalles
        ]


# =============================================================================
# CONSTANTES DE TARIFAS UNE PRECARGADAS (ERS sección 5.2)
# =============================================================================

TARIFAS_UNE_DEFAULT: list[dict[str, float | None]] = [
    {"limite_min": 0, "limite_max": 100, "precio_kwh": 0.40},
    {"limite_min": 100, "limite_max": 150, "precio_kwh": 1.30},
    {"limite_min": 150, "limite_max": 200, "precio_kwh": 1.75},
    {"limite_min": 200, "limite_max": 250, "precio_kwh": 3.00},
    {"limite_min": 250, "limite_max": 300, "precio_kwh": 4.00},
    {"limite_min": 300, "limite_max": 350, "precio_kwh": 7.50},
    {"limite_min": 350, "limite_max": 400, "precio_kwh": 9.00},
    {"limite_min": 400, "limite_max": 450, "precio_kwh": 10.00},
    {"limite_min": 450, "limite_max": 500, "precio_kwh": 15.00},
    {"limite_min": 500, "limite_max": None, "precio_kwh": 25.00},
]
