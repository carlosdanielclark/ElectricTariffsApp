"""
Electric Tariffs App - Excepciones del Dominio
===============================================
Errores personalizados para lógica de negocio.
NUNCA importar flet o sqlite3 aquí.
"""


class ElectricTariffsError(Exception):
    """Excepción base de la aplicación."""
    pass


# =============================================================================
# ERRORES DE AUTENTICACIÓN
# =============================================================================

class CredencialesInvalidasError(ElectricTariffsError):
    """Usuario o contraseña incorrectos."""
    def __init__(self, mensaje: str = "Credenciales inválidas"):
        super().__init__(mensaje)


class UsuarioBloqueadoError(ElectricTariffsError):
    """Usuario bloqueado por intentos fallidos."""
    def __init__(self, segundos_restantes: int):
        self.segundos_restantes = segundos_restantes
        super().__init__(f"Usuario bloqueado. Espera {segundos_restantes} segundos.")


class UsuarioInactivoError(ElectricTariffsError):
    """Usuario desactivado por el administrador."""
    def __init__(self, mensaje: str = "Usuario desactivado"):
        super().__init__(mensaje)


class ContrasenaDebilError(ElectricTariffsError):
    """Contraseña no cumple requisitos mínimos."""
    def __init__(self, mensaje: str = "La contraseña debe tener al menos 6 caracteres y 1 número"):
        super().__init__(mensaje)


class SesionExpiradaError(ElectricTariffsError):
    """Sesión expirada por inactividad."""
    def __init__(self, mensaje: str = "Sesión expirada por inactividad"):
        super().__init__(mensaje)


# =============================================================================
# ERRORES DE USUARIO
# =============================================================================

class UsuarioYaExisteError(ElectricTariffsError):
    """Nombre de usuario ya registrado."""
    def __init__(self, username: str):
        super().__init__(f"El usuario '{username}' ya existe")


class UsuarioNoEncontradoError(ElectricTariffsError):
    """Usuario no existe en el sistema."""
    def __init__(self, identificador: str | int):
        super().__init__(f"Usuario no encontrado: {identificador}")


# =============================================================================
# ERRORES DE MEDIDOR
# =============================================================================

class MedidorNoEncontradoError(ElectricTariffsError):
    """Medidor no existe."""
    def __init__(self, medidor_id: int):
        super().__init__(f"Medidor no encontrado: ID {medidor_id}")


class EtiquetaDuplicadaError(ElectricTariffsError):
    """Etiqueta ya usada por otro medidor del mismo usuario."""
    def __init__(self, etiqueta: str):
        super().__init__(f"Ya tienes un medidor con la etiqueta '{etiqueta}'")


class MedidorConLecturasError(ElectricTariffsError):
    """Intento de eliminar medidor con lecturas (requiere confirmación)."""
    def __init__(self, medidor_id: int, cantidad_lecturas: int):
        self.cantidad_lecturas = cantidad_lecturas
        super().__init__(f"El medidor tiene {cantidad_lecturas} lecturas que serán eliminadas")


# =============================================================================
# ERRORES DE LECTURA
# =============================================================================

class LecturaNoEncontradaError(ElectricTariffsError):
    """Lectura no existe."""
    def __init__(self, lectura_id: int):
        super().__init__(f"Lectura no encontrada: ID {lectura_id}")


class FechaFuturaError(ElectricTariffsError):
    """Fecha fin no puede ser futura."""
    def __init__(self, mensaje: str = "La fecha no puede ser futura"):
        super().__init__(mensaje)


class PeriodoDuplicadoError(ElectricTariffsError):
    """Ya existe una lectura para ese período y medidor."""
    def __init__(self, fecha_inicio: str, fecha_fin: str):
        super().__init__(f"Ya existe una lectura para el período {fecha_inicio} - {fecha_fin}")


class LecturaIncoherenteError(ElectricTariffsError):
    """Lectura actual menor que anterior sin ser rollover válido."""
    def __init__(self, anterior: float, actual: float):
        super().__init__(
            f"Lectura actual ({actual}) no puede ser menor que la anterior ({anterior})"
        )


class LecturaRetroactivaInvalidaError(ElectricTariffsError):
    """Lectura retroactiva fuera de rango permitido."""
    def __init__(self, mensaje: str):
        super().__init__(mensaje)


class PermisoDenegadoError(ElectricTariffsError):
    """Usuario sin permisos para esta acción."""
    def __init__(self, mensaje: str = "No tienes permisos para realizar esta acción"):
        super().__init__(mensaje)


class TiempoEdicionExpiradoError(ElectricTariffsError):
    """Vinculado intentando editar después de 48 horas."""
    def __init__(self, horas_limite: int = 48):
        super().__init__(f"Solo puedes editar tus lecturas dentro de las primeras {horas_limite} horas")


# =============================================================================
# ERRORES DE ROLLOVER
# =============================================================================

class RolloverNoConfirmadoError(ElectricTariffsError):
    """Rollover detectado pero pendiente de confirmación."""
    def __init__(self, consumo_calculado: float):
        self.consumo_calculado = consumo_calculado
        super().__init__(
            f"Se detectó reinicio del medidor. Consumo calculado: {consumo_calculado} kWh. ¿Confirmar?"
        )


# =============================================================================
# ERRORES DE TARIFA
# =============================================================================

class TramosInvalidosError(ElectricTariffsError):
    """Tramos no consecutivos o con solapamiento."""
    def __init__(self, mensaje: str = "Los tramos de tarifa deben ser consecutivos sin solapamiento"):
        super().__init__(mensaje)


# =============================================================================
# ERRORES DE VINCULACIÓN
# =============================================================================

class VinculacionYaExisteError(ElectricTariffsError):
    """Usuario ya vinculado a ese medidor."""
    def __init__(self, usuario_id: int, medidor_id: int):
        super().__init__(f"Usuario {usuario_id} ya está vinculado al medidor {medidor_id}")


class VinculacionNoEncontradaError(ElectricTariffsError):
    """Vinculación no existe."""
    def __init__(self, usuario_id: int, medidor_id: int):
        super().__init__(f"No existe vinculación entre usuario {usuario_id} y medidor {medidor_id}")


# =============================================================================
# ERRORES DE BACKUP/RESTORE
# =============================================================================

class BackupError(ElectricTariffsError):
    """Error al crear backup."""
    def __init__(self, mensaje: str = "Error al crear backup"):
        super().__init__(mensaje)


class RestoreError(ElectricTariffsError):
    """Error al restaurar backup."""
    def __init__(self, mensaje: str = "Error al restaurar backup"):
        super().__init__(mensaje)


class ArchivoBackupInvalidoError(ElectricTariffsError):
    """Archivo de backup corrupto o incompatible."""
    def __init__(self, mensaje: str = "Archivo de backup inválido o corrupto"):
        super().__init__(mensaje)
