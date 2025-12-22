"""
Electric Tariffs App - Sistema de Logs
======================================
Registro de eventos en CSV según RF-66/RF-67.
Formato: timestamp, usuario_id, evento, detalles
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional

from core.config import LOG_FULL_PATH
from core.models import TipoEvento, EventoLog


# =============================================================================
# CONSTANTES
# =============================================================================

CSV_HEADERS = ["timestamp", "usuario_id", "evento", "detalles"]


# =============================================================================
# GESTOR DE LOGS
# =============================================================================

class LogManager:
    """
    Gestor de logs de actividad.
    Escribe eventos en formato CSV legible en Excel (RNF-04).
    """
    
    _instance: Optional["LogManager"] = None
    
    def __new__(cls) -> "LogManager":
        """Singleton para asegurar una única instancia."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        self._log_path = LOG_FULL_PATH
        self._ensure_log_file()
        self._initialized = True
    
    def _ensure_log_file(self) -> None:
        """Crea archivo de log con headers si no existe."""
        if not self._log_path.exists():
            with open(self._log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
    
    def log(
        self,
        evento: TipoEvento,
        usuario_id: Optional[int] = None,
        detalles: str = ""
    ) -> None:
        """
        Registra un evento en el log.
        
        Args:
            evento: Tipo de evento (TipoEvento)
            usuario_id: ID del usuario que generó el evento (opcional)
            detalles: Información adicional del evento
        """
        registro = EventoLog(
            timestamp=datetime.now(),
            usuario_id=usuario_id,
            evento=evento,
            detalles=detalles
        )
        
        with open(self._log_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(registro.to_csv_row())
    
    def log_login(self, usuario_id: int, username: str) -> None:
        """Registra login exitoso."""
        self.log(TipoEvento.LOGIN, usuario_id, f"Usuario: {username}")
    
    def log_login_fallido(self, username: str, intentos: int) -> None:
        """Registra intento de login fallido."""
        self.log(TipoEvento.LOGIN_FALLIDO, None, f"Usuario: {username}, Intentos: {intentos}")
    
    def log_logout(self, usuario_id: int) -> None:
        """Registra cierre de sesión."""
        self.log(TipoEvento.LOGOUT, usuario_id)
    
    def log_lectura_creada(
        self,
        usuario_id: int,
        medidor_id: int,
        consumo: float,
        importe: float
    ) -> None:
        """Registra creación de lectura."""
        self.log(
            TipoEvento.LECTURA_CREADA,
            usuario_id,
            f"Medidor: {medidor_id}, Consumo: {consumo} kWh, Importe: ${round(importe)} CUP"
        )
    
    def log_lectura_editada(
        self,
        usuario_id: int,
        lectura_id: int,
        cambios: str
    ) -> None:
        """Registra edición de lectura."""
        self.log(TipoEvento.LECTURA_EDITADA, usuario_id, f"Lectura ID: {lectura_id}, {cambios}")
    
    def log_lectura_eliminada(self, usuario_id: int, lectura_id: int) -> None:
        """Registra eliminación de lectura."""
        self.log(TipoEvento.LECTURA_ELIMINADA, usuario_id, f"Lectura ID: {lectura_id}")
    
    def log_rollover(
        self,
        usuario_id: int,
        medidor_id: int,
        lectura_anterior: float,
        lectura_actual: float,
        consumo: float
    ) -> None:
        """Registra detección de rollover."""
        self.log(
            TipoEvento.ROLLOVER_DETECTADO,
            usuario_id,
            f"Medidor: {medidor_id}, Anterior: {lectura_anterior}, Actual: {lectura_actual}, "
            f"Consumo calculado: {consumo} kWh"
        )
    
    def log_tarifa_modificada(self, usuario_id: int, accion: str, detalles: str) -> None:
        """Registra modificación de tarifas."""
        self.log(TipoEvento.TARIFA_MODIFICADA, usuario_id, f"{accion}: {detalles}")
    
    def log_usuario_creado(self, admin_id: Optional[int], nuevo_usuario: str) -> None:
        """Registra creación de usuario."""
        self.log(TipoEvento.USUARIO_CREADO, admin_id, f"Nuevo usuario: {nuevo_usuario}")
    
    def log_usuario_desactivado(self, admin_id: int, usuario_id: int) -> None:
        """Registra desactivación de usuario."""
        self.log(TipoEvento.USUARIO_DESACTIVADO, admin_id, f"Usuario desactivado ID: {usuario_id}")
    
    def log_usuario_transferido(
        self,
        admin_id: int,
        usuario_id: int,
        cantidad_medidores: int
    ) -> None:
        """Registra transferencia de medidores de usuario eliminado."""
        self.log(
            TipoEvento.USUARIO_TRANSFERIDO,
            admin_id,
            f"Usuario eliminado ID: {usuario_id}, Medidores transferidos: {cantidad_medidores}"
        )
    
    def log_backup_creado(self, usuario_id: int, ruta: str) -> None:
        """Registra creación de backup."""
        self.log(TipoEvento.BACKUP_CREADO, usuario_id, f"Ruta: {ruta}")
    
    def log_backup_restaurado(self, usuario_id: int, ruta: str) -> None:
        """Registra restauración de backup."""
        self.log(TipoEvento.BACKUP_RESTAURADO, usuario_id, f"Desde: {ruta}")
    
    def log_medidor_creado(self, usuario_id: int, etiqueta: str) -> None:
        """Registra creación de medidor."""
        self.log(TipoEvento.MEDIDOR_CREADO, usuario_id, f"Etiqueta: {etiqueta}")
    
    def log_medidor_eliminado(self, usuario_id: int, medidor_id: int, etiqueta: str) -> None:
        """Registra eliminación de medidor."""
        self.log(TipoEvento.MEDIDOR_ELIMINADO, usuario_id, f"ID: {medidor_id}, Etiqueta: {etiqueta}")
    
    def log_vinculacion_creada(
        self,
        admin_id: int,
        usuario_id: int,
        medidor_id: int
    ) -> None:
        """Registra creación de vinculación."""
        self.log(
            TipoEvento.VINCULACION_CREADA,
            admin_id,
            f"Usuario: {usuario_id} vinculado a Medidor: {medidor_id}"
        )
    
    def log_vinculacion_eliminada(
        self,
        admin_id: int,
        usuario_id: int,
        medidor_id: int
    ) -> None:
        """Registra eliminación de vinculación."""
        self.log(
            TipoEvento.VINCULACION_ELIMINADA,
            admin_id,
            f"Usuario: {usuario_id} desvinculado de Medidor: {medidor_id}"
        )
    
    def log_password_cambiado(self, usuario_id: int) -> None:
        """Registra cambio de contraseña."""
        self.log(TipoEvento.PASSWORD_CAMBIADO, usuario_id)
    
    def log_password_reseteado(self, admin_id: int, usuario_id: int) -> None:
        """Registra reset de contraseña por admin."""
        self.log(TipoEvento.PASSWORD_RESETEADO, admin_id, f"Usuario reseteado ID: {usuario_id}")


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_logger() -> LogManager:
    """Obtiene instancia del gestor de logs."""
    return LogManager()
