"""
Electric Tariffs App - Estado Global de la Aplicación
=====================================================
Singleton que mantiene el estado compartido:
- Usuario logueado
- Configuración de sesión
- Control de inactividad (RF-12: 3 horas)
"""

from datetime import datetime, timedelta
from typing import Optional, Callable
import asyncio

from core.models import Usuario, TemaPreferido
from core.config import SESSION_TIMEOUT_HOURS


class AppState:
    """
    Estado global de la aplicación (Singleton).
    Gestiona sesión de usuario y preferencias.
    """
    
    _instance: Optional["AppState"] = None
    
    def __new__(cls) -> "AppState":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if self._initialized:
            return
        
        self._usuario_actual: Optional[Usuario] = None
        self._ultima_actividad: Optional[datetime] = None
        self._tema_actual: TemaPreferido = TemaPreferido.OSCURO
        self._on_logout_callback: Optional[Callable] = None
        self._on_theme_change_callback: Optional[Callable] = None
        self._initialized = True
    
    # =========================================================================
    # GESTIÓN DE SESIÓN
    # =========================================================================
    
    def login(self, usuario: Usuario) -> None:
        """
        Establece el usuario logueado.
        
        Args:
            usuario: Usuario autenticado
        """
        self._usuario_actual = usuario
        self._ultima_actividad = datetime.now()
        self._tema_actual = usuario.tema_preferido
    
    def logout(self) -> None:
        """Cierra la sesión actual."""
        self._usuario_actual = None
        self._ultima_actividad = None
        if self._on_logout_callback:
            self._on_logout_callback()
    
    def registrar_actividad(self) -> None:
        """Actualiza timestamp de última actividad."""
        if self._usuario_actual:
            self._ultima_actividad = datetime.now()
    
    def verificar_sesion_activa(self) -> bool:
        """
        Verifica si la sesión sigue activa (RF-12: 3 horas).
        
        Returns:
            True si sesión activa, False si expiró
        """
        if not self._usuario_actual or not self._ultima_actividad:
            return False
        
        tiempo_inactivo = datetime.now() - self._ultima_actividad
        limite = timedelta(hours=SESSION_TIMEOUT_HOURS)
        
        if tiempo_inactivo > limite:
            self.logout()
            return False
        
        return True
    
    # =========================================================================
    # PROPIEDADES
    # =========================================================================
    
    @property
    def usuario_actual(self) -> Optional[Usuario]:
        """Usuario actualmente logueado."""
        return self._usuario_actual
    
    @property
    def esta_logueado(self) -> bool:
        """Verifica si hay usuario logueado con sesión válida."""
        return self.verificar_sesion_activa()
    
    @property
    def es_admin(self) -> bool:
        """Verifica si el usuario actual es admin."""
        if not self._usuario_actual:
            return False
        return self._usuario_actual.es_admin
    
    @property
    def usuario_id(self) -> Optional[int]:
        """ID del usuario actual."""
        if not self._usuario_actual:
            return None
        return self._usuario_actual.id
    
    @property
    def tema_actual(self) -> TemaPreferido:
        """Tema visual actual."""
        return self._tema_actual
    
    @tema_actual.setter
    def tema_actual(self, tema: TemaPreferido) -> None:
        """Cambia el tema y notifica."""
        self._tema_actual = tema
        if self._on_theme_change_callback:
            self._on_theme_change_callback(tema)
    
    @property
    def debe_cambiar_password(self) -> bool:
        """Verifica si usuario debe cambiar contraseña (RF-02)."""
        if not self._usuario_actual:
            return False
        return self._usuario_actual.debe_cambiar_pass
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def set_logout_callback(self, callback: Callable) -> None:
        """Establece callback para cuando se cierre sesión."""
        self._on_logout_callback = callback
    
    def set_theme_change_callback(self, callback: Callable) -> None:
        """Establece callback para cuando cambie el tema."""
        self._on_theme_change_callback = callback


# =============================================================================
# FUNCIÓN DE ACCESO GLOBAL
# =============================================================================

def get_app_state() -> AppState:
    """Obtiene la instancia del estado global."""
    return AppState()
