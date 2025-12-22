"""
Electric Tariffs App - Core (Dominio)
=====================================
Capa de lógica pura. NUNCA importar flet o sqlite3.
"""

from core.models import (
    Usuario,
    Medidor,
    Vinculacion,
    Tarifa,
    Lectura,
    EventoLog,
    RolUsuario,
    EstadoUsuario,
    TemaPreferido,
    TipoEvento,
    TARIFAS_UNE_DEFAULT,
)

from core.errors import (
    ElectricTariffsError,
    CredencialesInvalidasError,
    UsuarioBloqueadoError,
    UsuarioInactivoError,
    ContrasenaDebilError,
    MedidorNoEncontradoError,
    LecturaIncoherenteError,
    RolloverNoConfirmadoError,
    PermisoDenegadoError,
)

from core.actions import (
    # Algoritmos críticos
    calcular_importe,
    calcular_importe_redondeado,
    detectar_rollover,
    calcular_consumo,
    recalcular_lecturas_afectadas,
    # Validaciones
    validar_password,
    hash_password,
    verificar_password,
    autenticar_usuario,
    verificar_permiso_edicion_lectura,
    verificar_permiso_eliminacion_lectura,
)

__all__ = [
    # Models
    "Usuario",
    "Medidor",
    "Vinculacion",
    "Tarifa",
    "Lectura",
    "EventoLog",
    "RolUsuario",
    "EstadoUsuario",
    "TemaPreferido",
    "TipoEvento",
    "TARIFAS_UNE_DEFAULT",
    # Errors
    "ElectricTariffsError",
    "CredencialesInvalidasError",
    "UsuarioBloqueadoError",
    "UsuarioInactivoError",
    "ContrasenaDebilError",
    "MedidorNoEncontradoError",
    "LecturaIncoherenteError",
    "RolloverNoConfirmadoError",
    "PermisoDenegadoError",
    # Actions
    "calcular_importe",
    "calcular_importe_redondeado",
    "detectar_rollover",
    "calcular_consumo",
    "recalcular_lecturas_afectadas",
    "validar_password",
    "hash_password",
    "verificar_password",
    "autenticar_usuario",
    "verificar_permiso_edicion_lectura",
    "verificar_permiso_eliminacion_lectura",
]
