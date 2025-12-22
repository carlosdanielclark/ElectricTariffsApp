"""
Electric Tariffs App - ViewModel de Medidores
============================================
Gestiona CRUD de medidores según RF-13 a RF-17.
"""

from typing import Optional, Tuple, List

from core.models import Medidor
from core.errors import (
    MedidorNoEncontradoError,
    EtiquetaDuplicadaError,
    MedidorConLecturasError,
)
from data.repositories import MedidorRepository
from data.logger import get_logger
from ui.app_state import get_app_state


class MedidorViewModel:
    """
    ViewModel para gestión de medidores.
    Implementa RF-13 a RF-17.
    """
    
    def __init__(self) -> None:
        self._medidor_repo = MedidorRepository()
        self._logger = get_logger()
        self._app_state = get_app_state()
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    def obtener_medidores_usuario(self) -> List[Medidor]:
        """
        Obtiene medidores accesibles por el usuario actual.
        Incluye propios + vinculados.
        
        Returns:
            Lista de medidores
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return []
        
        return self._medidor_repo.get_accesibles_por_usuario(usuario_id)
    
    def obtener_medidores_propios(self) -> List[Medidor]:
        """
        Obtiene solo los medidores donde el usuario es propietario.
        
        Returns:
            Lista de medidores propios
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return []
        
        return self._medidor_repo.get_by_propietario(usuario_id)
    
    def obtener_medidor(self, medidor_id: int) -> Optional[Medidor]:
        """
        Obtiene un medidor por ID.
        
        Args:
            medidor_id: ID del medidor
            
        Returns:
            Medidor o None si no existe
        """
        try:
            return self._medidor_repo.get_by_id(medidor_id)
        except MedidorNoEncontradoError:
            return None
    
    def es_propietario(self, medidor_id: int) -> bool:
        """
        Verifica si el usuario actual es propietario del medidor.
        
        Args:
            medidor_id: ID del medidor
            
        Returns:
            True si es propietario
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False
        
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            return medidor.propietario_id == usuario_id
        except MedidorNoEncontradoError:
            return False
    
    # =========================================================================
    # CRUD
    # =========================================================================
    
    def crear_medidor(
        self,
        etiqueta: str,
        numero_serie: Optional[str] = None,
        umbral_alerta: Optional[float] = None
    ) -> Tuple[bool, str, Optional[Medidor]]:
        """
        Crea un nuevo medidor (RF-13, RF-14).
        
        Args:
            etiqueta: Nombre/etiqueta obligatoria
            numero_serie: Número de serie (opcional)
            umbral_alerta: kWh para alerta (opcional)
            
        Returns:
            Tupla (éxito, mensaje, medidor_creado)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa.", None
        
        # Validaciones
        etiqueta = etiqueta.strip()
        if not etiqueta:
            return False, "La etiqueta es obligatoria.", None
        
        if len(etiqueta) > 50:
            return False, "La etiqueta no puede exceder 50 caracteres.", None
        
        if numero_serie:
            numero_serie = numero_serie.strip()
        
        if umbral_alerta is not None and umbral_alerta <= 0:
            return False, "El umbral de alerta debe ser mayor a 0.", None
        
        try:
            medidor = Medidor(
                propietario_id=usuario_id,
                etiqueta=etiqueta,
                numero_serie=numero_serie if numero_serie else None,
                umbral_alerta=umbral_alerta,
            )
            
            medidor_creado = self._medidor_repo.create(medidor)
            
            # Log
            self._logger.log_medidor_creado(usuario_id, etiqueta)
            
            return True, "Medidor creado exitosamente.", medidor_creado
            
        except EtiquetaDuplicadaError:
            return False, f"Ya tienes un medidor con la etiqueta '{etiqueta}'.", None
        except ValueError as e:
            return False, str(e), None
        except Exception as e:
            return False, f"Error al crear medidor: {str(e)}", None
    
    def actualizar_medidor(
        self,
        medidor_id: int,
        etiqueta: str,
        numero_serie: Optional[str] = None,
        umbral_alerta: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Actualiza un medidor existente (RF-15).
        
        Args:
            medidor_id: ID del medidor
            etiqueta: Nueva etiqueta
            numero_serie: Nuevo número de serie
            umbral_alerta: Nuevo umbral
            
        Returns:
            Tupla (éxito, mensaje)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa."
        
        # Validaciones
        etiqueta = etiqueta.strip()
        if not etiqueta:
            return False, "La etiqueta es obligatoria."
        
        if numero_serie:
            numero_serie = numero_serie.strip()
        
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            
            # Verificar permisos (RF-15: solo propietario/admin puede editar serie)
            es_propietario = medidor.propietario_id == usuario_id
            es_admin = self._app_state.es_admin
            
            if not es_propietario and not es_admin:
                return False, "No tienes permisos para editar este medidor."
            
            # Actualizar
            medidor.etiqueta = etiqueta
            medidor.numero_serie = numero_serie if numero_serie else None
            medidor.umbral_alerta = umbral_alerta
            
            self._medidor_repo.update(medidor)
            
            return True, "Medidor actualizado exitosamente."
            
        except MedidorNoEncontradoError:
            return False, "Medidor no encontrado."
        except EtiquetaDuplicadaError:
            return False, f"Ya tienes un medidor con la etiqueta '{etiqueta}'."
        except Exception as e:
            return False, f"Error al actualizar: {str(e)}"
    
    def eliminar_medidor(
        self,
        medidor_id: int,
        confirmar: bool = False
    ) -> Tuple[bool, str, Optional[int]]:
        """
        Elimina un medidor (RF-17).
        
        Args:
            medidor_id: ID del medidor
            confirmar: Si True, procede con eliminación
            
        Returns:
            Tupla (éxito, mensaje, cantidad_lecturas_afectadas)
            Si requiere confirmación: (False, mensaje_advertencia, cantidad)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa.", None
        
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            
            # Verificar permisos
            es_propietario = medidor.propietario_id == usuario_id
            es_admin = self._app_state.es_admin
            
            if not es_propietario and not es_admin:
                return False, "No tienes permisos para eliminar este medidor.", None
            
            # Contar lecturas
            cantidad_lecturas = self._medidor_repo.contar_lecturas(medidor_id)
            
            # Si tiene lecturas y no se ha confirmado, pedir confirmación (RF-17)
            if cantidad_lecturas > 0 and not confirmar:
                return (
                    False,
                    f"Este medidor tiene {cantidad_lecturas} lectura(s) que serán eliminadas. "
                    "¿Deseas continuar?",
                    cantidad_lecturas
                )
            
            # Proceder con eliminación
            etiqueta = medidor.etiqueta
            self._medidor_repo.delete(medidor_id)
            
            # Log
            self._logger.log_medidor_eliminado(usuario_id, medidor_id, etiqueta)
            
            return True, "Medidor eliminado exitosamente.", cantidad_lecturas
            
        except MedidorNoEncontradoError:
            return False, "Medidor no encontrado.", None
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}", None
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def obtener_estadisticas_medidor(self, medidor_id: int) -> dict:
        """
        Obtiene estadísticas básicas de un medidor.
        
        Args:
            medidor_id: ID del medidor
            
        Returns:
            Dict con cantidad_lecturas y tiene_alerta
        """
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            cantidad = self._medidor_repo.contar_lecturas(medidor_id)
            
            return {
                "cantidad_lecturas": cantidad,
                "tiene_umbral": medidor.umbral_alerta is not None,
                "umbral": medidor.umbral_alerta,
            }
        except MedidorNoEncontradoError:
            return {
                "cantidad_lecturas": 0,
                "tiene_umbral": False,
                "umbral": None,
            }
