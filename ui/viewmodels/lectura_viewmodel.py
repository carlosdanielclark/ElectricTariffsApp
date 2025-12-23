"""
Electric Tariffs App - ViewModel de Lecturas
============================================
Gestiona CRUD de lecturas según RF-24 a RF-40.
Implementa detección de rollover y recálculo en cascada.
"""

from datetime import date, datetime, timedelta
from typing import Optional, Tuple, List

from core.models import Lectura, Medidor
from core.actions import (
    calcular_importe,
    calcular_importe_redondeado,
    detectar_rollover,
    calcular_consumo,
    recalcular_lecturas_afectadas,
    verificar_permiso_edicion_lectura,
    verificar_permiso_eliminacion_lectura,
    verificar_alerta_umbral,
    ResultadoRollover,
)
from core.errors import (
    LecturaNoEncontradaError,
    PeriodoDuplicadoError,
    FechaFuturaError,
    LecturaIncoherenteError,
)
from data.repositories import LecturaRepository, MedidorRepository, TarifaRepository
from data.logger import get_logger
from ui.app_state import get_app_state


class LecturaViewModel:
    """
    ViewModel para gestión de lecturas.
    Implementa RF-24 a RF-40.
    """
    
    def __init__(self) -> None:
        self._lectura_repo = LecturaRepository()
        self._medidor_repo = MedidorRepository()
        self._tarifa_repo = TarifaRepository()
        self._logger = get_logger()
        self._app_state = get_app_state()
    
    # =========================================================================
    # CONSULTAS
    # =========================================================================
    
    def obtener_lecturas_medidor(
        self,
        medidor_id: int,
        anio: Optional[int] = None
    ) -> List[Lectura]:
        """
        Obtiene lecturas de un medidor.
        
        Args:
            medidor_id: ID del medidor
            anio: Año opcional para filtrar
            
        Returns:
            Lista de lecturas ordenadas cronológicamente
        """
        return self._lectura_repo.get_by_medidor(medidor_id, anio)
    
    def obtener_lectura(self, lectura_id: int) -> Optional[Lectura]:
        """Obtiene una lectura por ID."""
        try:
            return self._lectura_repo.get_by_id(lectura_id)
        except LecturaNoEncontradaError:
            return None
    
    def obtener_ultima_lectura(self, medidor_id: int) -> Optional[Lectura]:
        """Obtiene la última lectura para precarga."""
        return self._lectura_repo.get_ultima_lectura(medidor_id)
    
    def obtener_anios_disponibles(self, medidor_id: int) -> List[int]:
        """Obtiene años con lecturas registradas."""
        anios = self._lectura_repo.get_anios_con_datos(medidor_id)
        if not anios:
            anios = [date.today().year]
        return anios
    
    def obtener_ultimas_lecturas(
        self,
        medidor_id: int,
        cantidad: int = 6
    ) -> List[Lectura]:
        """Obtiene últimas N lecturas para gráfico."""
        return self._lectura_repo.get_ultimos_n_meses(medidor_id, cantidad)
    
    # =========================================================================
    # PRECÁLCULO (RF-25, RF-26)
    # =========================================================================
    
    def precalcular_lectura(
        self,
        medidor_id: int,
        lectura_actual: float,
        fecha_fin: date,
        confirmar_rollover: bool = False
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Precalcula consumo e importe antes de guardar (RF-25).
        
        Args:
            medidor_id: ID del medidor
            lectura_actual: Valor leído del medidor
            fecha_fin: Fecha de la lectura
            confirmar_rollover: Si True, acepta rollover automático
            
        Returns:
            Tupla (éxito, mensaje, datos_precalculo)
            datos_precalculo: {
                lectura_anterior, consumo, importe, importe_redondeado,
                es_rollover, requiere_confirmacion, mensaje_rollover
            }
        """
        # Validar fecha no futura (RF-29)
        if fecha_fin > date.today():
            return False, "No se permiten fechas futuras.", None
        
        # Obtener lectura anterior
        lectura_previa = self._lectura_repo.get_lectura_anterior_cronologica(
            medidor_id, fecha_fin
        )
        
        lectura_anterior = 0.0
        if lectura_previa:
            lectura_anterior = lectura_previa.lectura_actual
        
        # Detectar rollover (RF-27)
        resultado_rollover = detectar_rollover(lectura_anterior, lectura_actual)
        
        # Si hay rollover no confirmado y requiere confirmación
        if resultado_rollover.requiere_confirmacion and not confirmar_rollover:
            return False, resultado_rollover.mensaje, {
                "lectura_anterior": lectura_anterior,
                "consumo": resultado_rollover.consumo,
                "es_rollover": resultado_rollover.es_rollover,
                "requiere_confirmacion": True,
                "mensaje_rollover": resultado_rollover.mensaje,
            }
        
        # Si es inconsistente (menor sin ser rollover) y no confirmado
        if not resultado_rollover.es_rollover and lectura_actual < lectura_anterior:
            if not confirmar_rollover:
                return False, resultado_rollover.mensaje, {
                    "lectura_anterior": lectura_anterior,
                    "consumo": 0,
                    "es_rollover": False,
                    "requiere_confirmacion": True,
                    "mensaje_rollover": resultado_rollover.mensaje,
                }
        
        # Calcular consumo
        consumo = resultado_rollover.consumo
        
        # Calcular importe con tarifas
        tarifas = self._tarifa_repo.get_all()
        importe = calcular_importe(consumo, tarifas)
        importe_redondeado = calcular_importe_redondeado(consumo, tarifas)
        
        return True, "Cálculo exitoso", {
            "lectura_anterior": lectura_anterior,
            "consumo": consumo,
            "importe": importe,
            "importe_redondeado": importe_redondeado,
            "es_rollover": resultado_rollover.es_rollover,
            "requiere_confirmacion": False,
            "mensaje_rollover": resultado_rollover.mensaje if resultado_rollover.es_rollover else None,
        }
    
    # =========================================================================
    # CRUD
    # =========================================================================
    
    def crear_lectura(
        self,
        medidor_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        lectura_actual: float,
        confirmar_rollover: bool = False
    ) -> Tuple[bool, str, Optional[Lectura], Optional[str]]:
        """
        Crea una nueva lectura (RF-24).
        
        Args:
            medidor_id: ID del medidor
            fecha_inicio: Fecha inicio del período
            fecha_fin: Fecha fin del período
            lectura_actual: Valor del medidor
            confirmar_rollover: Si acepta rollover
            
        Returns:
            Tupla (éxito, mensaje, lectura_creada, alerta_umbral)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa.", None, None
        
        # Validar fecha no futura
        if fecha_fin > date.today():
            return False, "No se permiten fechas futuras.", None, None
        
        if fecha_inicio > fecha_fin:
            return False, "La fecha de inicio no puede ser posterior a la fecha fin.", None, None
        
        # Verificar período duplicado
        if self._lectura_repo.existe_periodo(medidor_id, fecha_inicio, fecha_fin):
            return False, "Ya existe una lectura para este período.", None, None
        
        # Precalcular
        exito, mensaje, datos = self.precalcular_lectura(
            medidor_id, lectura_actual, fecha_fin, confirmar_rollover
        )
        
        if not exito:
            return False, mensaje, None, None
        
        if datos.get("requiere_confirmacion"):
            return False, datos.get("mensaje_rollover", "Requiere confirmación"), None, None
        
        try:
            # Crear lectura
            lectura = Lectura(
                medidor_id=medidor_id,
                autor_user_id=usuario_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                lectura_anterior=datos["lectura_anterior"],
                lectura_actual=lectura_actual,
                consumo_kwh=datos["consumo"],
                importe_total=datos["importe"],
                es_rollover=datos["es_rollover"],
            )
            
            lectura_creada = self._lectura_repo.create(lectura)
            
            # Verificar si hay lecturas posteriores que recalcular (efecto dominó)
            self._aplicar_efecto_domino(medidor_id, fecha_fin)
            
            # Log
            self._logger.log_lectura_creada(
                usuario_id, medidor_id, lectura_creada.consumo_kwh, lectura_creada.importe_total
            )
            
            # Verificar alerta de umbral (RF-52)
            alerta = self._verificar_alerta_umbral(medidor_id, datos["consumo"])
            
            return True, "Lectura registrada exitosamente.", lectura_creada, alerta
            
        except PeriodoDuplicadoError:
            return False, "Ya existe una lectura para este período.", None, None
        except Exception as e:
            return False, f"Error al crear lectura: {str(e)}", None, None
    
    def actualizar_lectura(
        self,
        lectura_id: int,
        lectura_actual: float,
        confirmar_rollover: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Actualiza una lectura existente (RF-30 a RF-34).
        
        Args:
            lectura_id: ID de la lectura
            lectura_actual: Nuevo valor
            confirmar_rollover: Si acepta rollover
            
        Returns:
            Tupla (éxito, mensaje, alerta_umbral)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa.", None
        
        try:
            lectura = self._lectura_repo.get_by_id(lectura_id)
        except LecturaNoEncontradaError:
            return False, "Lectura no encontrada.", None
        
        # Verificar permisos (RF-31, RF-32)
        usuario = self._app_state.usuario_actual
        puede_editar, mensaje_permiso = verificar_permiso_edicion_lectura(
            usuario=usuario,
            lectura=lectura,
            es_propietario_medidor=self._es_propietario_medidor(lectura.medidor_id)
        )
        
        if not puede_editar:
            return False, mensaje_permiso, None
        
        # Precalcular con nuevo valor
        exito, mensaje, datos = self.precalcular_lectura(
            lectura.medidor_id, lectura_actual, lectura.fecha_fin, confirmar_rollover
        )
        
        if not exito:
            return False, mensaje, None
        
        if datos.get("requiere_confirmacion"):
            return False, datos.get("mensaje_rollover", "Requiere confirmación"), None
        
        try:
            # Actualizar
            lectura.lectura_actual = lectura_actual
            lectura.lectura_anterior = datos["lectura_anterior"]
            lectura.consumo_kwh = datos["consumo"]
            lectura.importe_total = datos["importe"]
            lectura.es_rollover = datos["es_rollover"]
            
            self._lectura_repo.update(lectura)
            
            # Aplicar efecto dominó (RF-33)
            self._aplicar_efecto_domino(lectura.medidor_id, lectura.fecha_fin)
            
            # Log
            self._logger.log_lectura_editada(
                usuario_id, lectura_id, f"Nueva lectura: {lectura_actual}"
            )
            
            # Verificar alerta
            alerta = self._verificar_alerta_umbral(lectura.medidor_id, datos["consumo"])
            
            return True, "Lectura actualizada exitosamente.", alerta
            
        except Exception as e:
            return False, f"Error al actualizar: {str(e)}", None
    
    def eliminar_lectura(self, lectura_id: int) -> Tuple[bool, str]:
        """
        Elimina una lectura (RF-35, RF-36).
        
        Args:
            lectura_id: ID de la lectura
            
        Returns:
            Tupla (éxito, mensaje)
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False, "No hay sesión activa."
        
        try:
            lectura = self._lectura_repo.get_by_id(lectura_id)
        except LecturaNoEncontradaError:
            return False, "Lectura no encontrada."
        
        # Verificar permisos (RF-35, RF-36)
        usuario = self._app_state.usuario_actual
        puede_eliminar, mensaje_permiso = verificar_permiso_eliminacion_lectura(
            usuario=usuario,
            lectura=lectura,
            es_propietario_medidor=self._es_propietario_medidor(lectura.medidor_id)
        )
        
        if not puede_eliminar:
            return False, mensaje_permiso
        
        medidor_id = lectura.medidor_id
        fecha_fin = lectura.fecha_fin
        
        try:
            self._lectura_repo.delete(lectura_id)
            
            # Recalcular lecturas posteriores
            self._aplicar_efecto_domino(medidor_id, fecha_fin)
            
            # Log
            self._logger.log_lectura_eliminada(usuario_id, lectura_id)
            
            return True, "Lectura eliminada exitosamente."
            
        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"
    
    # =========================================================================
    # EFECTO DOMINÓ (RF-33)
    # =========================================================================
    
    def _aplicar_efecto_domino(self, medidor_id: int, desde_fecha: date) -> None:
        """
        Recalcula lecturas posteriores a una fecha (efecto dominó).
        """
        # Obtener lecturas desde la fecha
        lecturas = self._lectura_repo.get_lecturas_desde(medidor_id, desde_fecha)
        
        if len(lecturas) <= 1:
            return  # No hay lecturas posteriores que recalcular
        
        tarifas = self._tarifa_repo.get_all()
        
        # Recalcular en cascada
        lecturas_modificadas = recalcular_lecturas_afectadas(
            lecturas, tarifas, desde_indice=1
        )
        
        # Guardar cambios
        for lectura in lecturas_modificadas:
            self._lectura_repo.update(lectura)
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def _es_propietario_medidor(self, medidor_id: int) -> bool:
        """Verifica si el usuario actual es propietario del medidor."""
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return False
        
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            return medidor.propietario_id == usuario_id
        except:
            return False
    
    def _verificar_alerta_umbral(
        self,
        medidor_id: int,
        consumo: float
    ) -> Optional[str]:
        """Verifica si el consumo supera el umbral configurado."""
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
            supera, mensaje = verificar_alerta_umbral(consumo, medidor.umbral_alerta)
            if supera:
                return mensaje
        except:
            pass
        return None
    
    def puede_editar_lectura(self, lectura: Lectura) -> bool:
        """Verifica si el usuario puede editar la lectura."""
        usuario = self._app_state.usuario_actual
        if not usuario:
            return False
        
        puede, _ = verificar_permiso_edicion_lectura(
            usuario=usuario,
            lectura=lectura,
            es_propietario_medidor=self._es_propietario_medidor(lectura.medidor_id)
        )
        return puede
    
    def puede_eliminar_lectura(self, lectura: Lectura) -> bool:
        """Verifica si el usuario puede eliminar la lectura."""
        usuario = self._app_state.usuario_actual
        if not usuario:
            return False
        
        puede, _ = verificar_permiso_eliminacion_lectura(
            usuario=usuario,
            lectura=lectura,
            es_propietario_medidor=self._es_propietario_medidor(lectura.medidor_id)
        )
        return puede
    
    def obtener_resumen_medidor(self, medidor_id: int) -> dict:
        """
        Obtiene resumen estadístico del medidor.
        
        Returns:
            Dict con total_lecturas, consumo_total, importe_total,
            consumo_mes_actual, importe_mes_actual
        """
        lecturas = self._lectura_repo.get_by_medidor(medidor_id)
        
        consumo_total = sum(l.consumo_kwh for l in lecturas)
        importe_total = sum(l.importe_total for l in lecturas)
        
        consumo_mes = self._lectura_repo.get_consumo_total_mes_actual(medidor_id)
        importe_mes = self._lectura_repo.get_importe_total_mes_actual(medidor_id)
        
        return {
            "total_lecturas": len(lecturas),
            "consumo_total": consumo_total,
            "importe_total": importe_total,
            "consumo_mes_actual": consumo_mes,
            "importe_mes_actual": importe_mes,
        }
