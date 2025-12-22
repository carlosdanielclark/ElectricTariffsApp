"""
Electric Tariffs App - ViewModel de Autenticación
=================================================
Gestiona lógica de Login, Registro y Recuperación.
Implementa RF-05 a RF-12.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from core.models import Usuario, RolUsuario, EstadoUsuario
from core.actions import (
    validar_password,
    hash_password,
    verificar_password,
    autenticar_usuario,
)
from core.errors import (
    ContrasenaDebilError,
    CredencialesInvalidasError,
    UsuarioInactivoError,
    UsuarioBloqueadoError,
    UsuarioYaExisteError,
)
from core.config import MAX_LOGIN_ATTEMPTS, LOCKOUT_MINUTES, RECOVERY_KEY_PATH
from data.repositories import UsuarioRepository
from data.logger import get_logger
from ui.app_state import get_app_state


class AuthViewModel:
    """
    ViewModel para autenticación.
    Maneja estado de login, intentos fallidos y bloqueos.
    """
    
    def __init__(self) -> None:
        self._usuario_repo = UsuarioRepository()
        self._logger = get_logger()
        self._app_state = get_app_state()
        
        # Control de intentos fallidos (RF-09)
        self._intentos_fallidos: dict[str, int] = {}
        self._bloqueos: dict[str, datetime] = {}
    
    # =========================================================================
    # LOGIN (RF-05, RF-09)
    # =========================================================================
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Intenta autenticar al usuario.
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Tupla (éxito, mensaje)
        """
        username = username.strip().lower()
        
        # Verificar bloqueo (RF-09)
        if self._esta_bloqueado(username):
            segundos = self._segundos_restantes_bloqueo(username)
            return False, f"Usuario bloqueado. Espera {segundos} segundos."
        
        try:
            # Buscar usuario
            usuario = self._usuario_repo.get_by_username(username)
            
            # Autenticar (verifica password y estado)
            usuario_auth = autenticar_usuario(usuario, password)
            
            # Login exitoso - resetear intentos
            self._resetear_intentos(username)
            
            # Establecer sesión
            self._app_state.login(usuario_auth)
            
            # Log
            self._logger.log_login(usuario_auth.id, username)
            
            # Verificar si debe cambiar contraseña (RF-02)
            if usuario_auth.debe_cambiar_pass:
                return True, "CAMBIAR_PASSWORD"
            
            return True, "Login exitoso"
            
        except CredencialesInvalidasError:
            self._registrar_intento_fallido(username)
            intentos = self._intentos_fallidos.get(username, 0)
            restantes = MAX_LOGIN_ATTEMPTS - intentos
            
            if restantes <= 0:
                self._bloquear_usuario(username)
                return False, f"Usuario bloqueado por {LOCKOUT_MINUTES} minuto(s)."
            
            return False, f"Credenciales inválidas. {restantes} intento(s) restante(s)."
            
        except UsuarioInactivoError:
            return False, "Usuario desactivado. Contacta al administrador."
            
        except Exception as e:
            return False, f"Error inesperado: {str(e)}"
    
    def logout(self) -> None:
        """Cierra la sesión actual."""
        if self._app_state.usuario_id:
            self._logger.log_logout(self._app_state.usuario_id)
        self._app_state.logout()
    
    # =========================================================================
    # REGISTRO (RF-06 a RF-08)
    # =========================================================================
    
    def registrar(
        self,
        nombre: str,
        username: str,
        password: str,
        confirmar_password: str
    ) -> Tuple[bool, str]:
        """
        Registra un nuevo usuario.
        
        Args:
            nombre: Nombre completo
            username: Nombre de usuario
            password: Contraseña
            confirmar_password: Confirmación de contraseña
            
        Returns:
            Tupla (éxito, mensaje)
        """
        # Validaciones básicas
        nombre = nombre.strip()
        username = username.strip().lower()
        
        if not nombre:
            return False, "El nombre es obligatorio."
        
        if not username:
            return False, "El usuario es obligatorio."
        
        if len(username) < 3:
            return False, "El usuario debe tener al menos 3 caracteres."
        
        if password != confirmar_password:
            return False, "Las contraseñas no coinciden."
        
        # Validar fortaleza de contraseña (RF-08)
        try:
            validar_password(password)
        except ContrasenaDebilError as e:
            return False, str(e)
        
        # Verificar usuario existente
        existente = self._usuario_repo.get_by_username(username)
        if existente:
            return False, f"El usuario '{username}' ya existe."
        
        try:
            # Crear usuario
            nuevo_usuario = Usuario(
                nombre=nombre,
                username=username,
                password_hash=hash_password(password),
                rol=RolUsuario.USER,
                estado=EstadoUsuario.ACTIVO,
                debe_cambiar_pass=False,
            )
            
            usuario_creado = self._usuario_repo.create(nuevo_usuario)
            
            # Log
            self._logger.log_usuario_creado(None, username)
            
            return True, "Cuenta creada exitosamente. Ahora puedes iniciar sesión."
            
        except UsuarioYaExisteError:
            return False, f"El usuario '{username}' ya existe."
        except Exception as e:
            return False, f"Error al crear cuenta: {str(e)}"
    
    # =========================================================================
    # CAMBIO DE CONTRASEÑA (RF-02, RF-11)
    # =========================================================================
    
    def cambiar_password(
        self,
        password_actual: str,
        nueva_password: str,
        confirmar_password: str
    ) -> Tuple[bool, str]:
        """
        Cambia la contraseña del usuario actual.
        
        Args:
            password_actual: Contraseña actual
            nueva_password: Nueva contraseña
            confirmar_password: Confirmación
            
        Returns:
            Tupla (éxito, mensaje)
        """
        usuario = self._app_state.usuario_actual
        if not usuario:
            return False, "No hay sesión activa."
        
        # Verificar contraseña actual
        if not verificar_password(password_actual, usuario.password_hash):
            return False, "La contraseña actual es incorrecta."
        
        if nueva_password != confirmar_password:
            return False, "Las contraseñas no coinciden."
        
        # Validar nueva contraseña
        try:
            validar_password(nueva_password)
        except ContrasenaDebilError as e:
            return False, str(e)
        
        try:
            # Actualizar
            nuevo_hash = hash_password(nueva_password)
            self._usuario_repo.update_password(usuario.id, nuevo_hash)
            
            # Actualizar estado local
            usuario.password_hash = nuevo_hash
            usuario.debe_cambiar_pass = False
            
            # Log
            self._logger.log_password_cambiado(usuario.id)
            
            return True, "Contraseña actualizada exitosamente."
            
        except Exception as e:
            return False, f"Error al cambiar contraseña: {str(e)}"
    
    # =========================================================================
    # RECUPERACIÓN ADMIN (RF-10)
    # =========================================================================
    
    def recuperar_admin(
        self,
        clave_recovery: str,
        nueva_password: str,
        confirmar_password: str
    ) -> Tuple[bool, str]:
        """
        Recupera acceso admin usando clave de recovery_key.txt (RF-10).
        
        Args:
            clave_recovery: Clave del archivo recovery_key.txt
            nueva_password: Nueva contraseña
            confirmar_password: Confirmación
            
        Returns:
            Tupla (éxito, mensaje)
        """
        # Leer clave del archivo
        try:
            contenido = RECOVERY_KEY_PATH.read_text()
            # Buscar línea que empieza con "CLAVE:"
            clave_real = None
            for linea in contenido.split("\n"):
                if linea.startswith("CLAVE:"):
                    clave_real = linea.replace("CLAVE:", "").strip()
                    break
            
            if not clave_real:
                return False, "Archivo de recuperación corrupto."
                
        except FileNotFoundError:
            return False, "Archivo de recuperación no encontrado."
        except Exception as e:
            return False, f"Error al leer archivo: {str(e)}"
        
        # Verificar clave
        if clave_recovery.strip() != clave_real:
            return False, "Clave de recuperación incorrecta."
        
        if nueva_password != confirmar_password:
            return False, "Las contraseñas no coinciden."
        
        # Validar nueva contraseña
        try:
            validar_password(nueva_password)
        except ContrasenaDebilError as e:
            return False, str(e)
        
        try:
            # Obtener admin
            admin = self._usuario_repo.get_by_username("admin")
            if not admin:
                return False, "Usuario admin no encontrado."
            
            # Actualizar contraseña
            nuevo_hash = hash_password(nueva_password)
            self._usuario_repo.update_password(admin.id, nuevo_hash)
            
            # Log
            self._logger.log_password_reseteado(admin.id, admin.id)
            
            return True, "Contraseña de administrador recuperada exitosamente."
            
        except Exception as e:
            return False, f"Error al recuperar: {str(e)}"
    
    # =========================================================================
    # CONTROL DE BLOQUEOS (RF-09)
    # =========================================================================
    
    def _esta_bloqueado(self, username: str) -> bool:
        """Verifica si el usuario está bloqueado."""
        if username not in self._bloqueos:
            return False
        
        tiempo_bloqueo = self._bloqueos[username]
        if datetime.now() > tiempo_bloqueo:
            # Bloqueo expirado
            del self._bloqueos[username]
            self._resetear_intentos(username)
            return False
        
        return True
    
    def _segundos_restantes_bloqueo(self, username: str) -> int:
        """Calcula segundos restantes de bloqueo."""
        if username not in self._bloqueos:
            return 0
        
        restante = self._bloqueos[username] - datetime.now()
        return max(0, int(restante.total_seconds()))
    
    def _registrar_intento_fallido(self, username: str) -> None:
        """Registra un intento de login fallido."""
        self._intentos_fallidos[username] = self._intentos_fallidos.get(username, 0) + 1
        self._logger.log_login_fallido(username, self._intentos_fallidos[username])
    
    def _bloquear_usuario(self, username: str) -> None:
        """Bloquea al usuario por el tiempo configurado."""
        self._bloqueos[username] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
    
    def _resetear_intentos(self, username: str) -> None:
        """Resetea contador de intentos fallidos."""
        if username in self._intentos_fallidos:
            del self._intentos_fallidos[username]
        if username in self._bloqueos:
            del self._bloqueos[username]
