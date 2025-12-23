"""
Electric Tariffs App - ViewModel de Dashboard
=============================================
Gestiona estadísticas y resumen del sistema.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any

from core.models import Medidor, Lectura
from core.actions import calcular_importe_redondeado
from data.repositories import (
    MedidorRepository,
    LecturaRepository,
    TarifaRepository,
    UsuarioRepository,
)
from ui.app_state import get_app_state


class DashboardViewModel:
    """
    ViewModel para dashboard y estadísticas.
    Proporciona datos agregados para visualización.
    """
    
    def __init__(self) -> None:
        self._medidor_repo = MedidorRepository()
        self._lectura_repo = LecturaRepository()
        self._tarifa_repo = TarifaRepository()
        self._usuario_repo = UsuarioRepository()
        self._app_state = get_app_state()
    
    # =========================================================================
    # ESTADÍSTICAS GENERALES
    # =========================================================================
    
    def obtener_resumen_general(self) -> Dict[str, Any]:
        """
        Obtiene resumen general para el usuario actual.
        
        Returns:
            Dict con estadísticas globales
        """
        usuario_id = self._app_state.usuario_id
        if not usuario_id:
            return self._resumen_vacio()
        
        # Obtener medidores accesibles
        medidores = self._medidor_repo.get_accesibles_por_usuario(usuario_id)
        
        total_medidores = len(medidores)
        total_lecturas = 0
        consumo_total = 0.0
        importe_total = 0.0
        consumo_mes = 0.0
        importe_mes = 0.0
        alertas = []
        
        for medidor in medidores:
            # Contar lecturas
            lecturas = self._lectura_repo.get_by_medidor(medidor.id)
            total_lecturas += len(lecturas)
            
            # Sumar consumos e importes
            for lectura in lecturas:
                consumo_total += lectura.consumo_kwh
                importe_total += lectura.importe_total
            
            # Mes actual
            consumo_mes += self._lectura_repo.get_consumo_total_mes_actual(medidor.id)
            importe_mes += self._lectura_repo.get_importe_total_mes_actual(medidor.id)
            
            # Verificar alertas de umbral
            if medidor.umbral_alerta:
                ultima = self._lectura_repo.get_ultima_lectura(medidor.id)
                if ultima and ultima.consumo_kwh > medidor.umbral_alerta:
                    alertas.append({
                        "medidor": medidor.etiqueta,
                        "consumo": ultima.consumo_kwh,
                        "umbral": medidor.umbral_alerta,
                    })
        
        return {
            "total_medidores": total_medidores,
            "total_lecturas": total_lecturas,
            "consumo_total": consumo_total,
            "importe_total": importe_total,
            "consumo_mes_actual": consumo_mes,
            "importe_mes_actual": importe_mes,
            "importe_mes_redondeado": round(importe_mes),
            "alertas": alertas,
            "tiene_alertas": len(alertas) > 0,
        }
    
    def _resumen_vacio(self) -> Dict[str, Any]:
        """Retorna resumen vacío."""
        return {
            "total_medidores": 0,
            "total_lecturas": 0,
            "consumo_total": 0.0,
            "importe_total": 0.0,
            "consumo_mes_actual": 0.0,
            "importe_mes_actual": 0.0,
            "importe_mes_redondeado": 0,
            "alertas": [],
            "tiene_alertas": False,
        }
    
    # =========================================================================
    # ESTADÍSTICAS POR MEDIDOR
    # =========================================================================
    
    def obtener_resumen_medidor(self, medidor_id: int) -> Dict[str, Any]:
        """
        Obtiene resumen de un medidor específico.
        
        Args:
            medidor_id: ID del medidor
            
        Returns:
            Dict con estadísticas del medidor
        """
        try:
            medidor = self._medidor_repo.get_by_id(medidor_id)
        except:
            return self._resumen_medidor_vacio()
        
        lecturas = self._lectura_repo.get_by_medidor(medidor_id)
        
        consumo_total = sum(l.consumo_kwh for l in lecturas)
        importe_total = sum(l.importe_total for l in lecturas)
        
        consumo_mes = self._lectura_repo.get_consumo_total_mes_actual(medidor_id)
        importe_mes = self._lectura_repo.get_importe_total_mes_actual(medidor_id)
        
        ultima_lectura = self._lectura_repo.get_ultima_lectura(medidor_id)
        
        # Calcular promedio mensual
        promedio_consumo = 0.0
        if lecturas:
            promedio_consumo = consumo_total / len(lecturas)
        
        # Verificar alerta
        alerta_activa = False
        if medidor.umbral_alerta and ultima_lectura:
            alerta_activa = ultima_lectura.consumo_kwh > medidor.umbral_alerta
        
        return {
            "medidor": medidor,
            "total_lecturas": len(lecturas),
            "consumo_total": consumo_total,
            "importe_total": importe_total,
            "consumo_mes_actual": consumo_mes,
            "importe_mes_actual": importe_mes,
            "importe_mes_redondeado": round(importe_mes),
            "promedio_consumo": promedio_consumo,
            "ultima_lectura": ultima_lectura,
            "alerta_activa": alerta_activa,
        }
    
    def _resumen_medidor_vacio(self) -> Dict[str, Any]:
        """Retorna resumen de medidor vacío."""
        return {
            "medidor": None,
            "total_lecturas": 0,
            "consumo_total": 0.0,
            "importe_total": 0.0,
            "consumo_mes_actual": 0.0,
            "importe_mes_actual": 0.0,
            "importe_mes_redondeado": 0,
            "promedio_consumo": 0.0,
            "ultima_lectura": None,
            "alerta_activa": False,
        }
    
    # =========================================================================
    # DATOS PARA GRÁFICOS
    # =========================================================================
    
    def obtener_datos_grafico_consumo(
        self,
        medidor_id: int,
        meses: int = 6
    ) -> Dict[str, List]:
        """
        Obtiene datos para gráfico de consumo.
        
        Args:
            medidor_id: ID del medidor
            meses: Cantidad de meses a mostrar
            
        Returns:
            Dict con labels y valores para gráfico
        """
        lecturas = self._lectura_repo.get_ultimos_n_meses(medidor_id, meses)
        
        labels = []
        consumos = []
        importes = []
        
        for lectura in lecturas:
            # Formato: "Ene 2025"
            if lectura.fecha_fin:
                label = lectura.fecha_fin.strftime("%b %Y")
            else:
                label = "N/A"
            
            labels.append(label)
            consumos.append(lectura.consumo_kwh)
            importes.append(round(lectura.importe_total))
        
        return {
            "labels": labels,
            "consumos": consumos,
            "importes": importes,
        }
    
    def obtener_datos_comparativa_anual(
        self,
        medidor_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene comparativa del año actual vs anterior.
        
        Returns:
            Dict con consumo e importe de ambos años
        """
        anio_actual = date.today().year
        anio_anterior = anio_actual - 1
        
        lecturas_actual = self._lectura_repo.get_by_medidor(medidor_id, anio_actual)
        lecturas_anterior = self._lectura_repo.get_by_medidor(medidor_id, anio_anterior)
        
        consumo_actual = sum(l.consumo_kwh for l in lecturas_actual)
        consumo_anterior = sum(l.consumo_kwh for l in lecturas_anterior)
        
        importe_actual = sum(l.importe_total for l in lecturas_actual)
        importe_anterior = sum(l.importe_total for l in lecturas_anterior)
        
        # Calcular variación
        variacion_consumo = 0.0
        variacion_importe = 0.0
        
        if consumo_anterior > 0:
            variacion_consumo = ((consumo_actual - consumo_anterior) / consumo_anterior) * 100
        
        if importe_anterior > 0:
            variacion_importe = ((importe_actual - importe_anterior) / importe_anterior) * 100
        
        return {
            "anio_actual": anio_actual,
            "anio_anterior": anio_anterior,
            "consumo_actual": consumo_actual,
            "consumo_anterior": consumo_anterior,
            "importe_actual": importe_actual,
            "importe_anterior": importe_anterior,
            "variacion_consumo": variacion_consumo,
            "variacion_importe": variacion_importe,
        }
    
    # =========================================================================
    # TARIFAS VIGENTES
    # =========================================================================
    
    def obtener_tarifas_vigentes(self) -> List[Dict[str, Any]]:
        """
        Obtiene tarifas actuales para visualización.
        
        Returns:
            Lista de dicts con info de tarifas
        """
        tarifas = self._tarifa_repo.get_all()
        
        return [
            {
                "tramo": f"{int(t.limite_min)}-{int(t.limite_max) if t.limite_max else '∞'}",
                "limite_min": t.limite_min,
                "limite_max": t.limite_max,
                "precio": t.precio_kwh,
            }
            for t in tarifas
        ]
    
    # =========================================================================
    # ADMIN: ESTADÍSTICAS GLOBALES
    # =========================================================================
    
    def obtener_estadisticas_admin(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas globales (solo admin).
        
        Returns:
            Dict con estadísticas del sistema completo
        """
        if not self._app_state.es_admin:
            return {}
        
        usuarios = self._usuario_repo.get_all()
        total_usuarios = len(usuarios)
        usuarios_activos = len([u for u in usuarios if u.estado.value == "ACTIVO"])
        
        # Contar todos los medidores
        total_medidores = 0
        total_lecturas = 0
        consumo_global = 0.0
        importe_global = 0.0
        
        for usuario in usuarios:
            medidores = self._medidor_repo.get_by_propietario(usuario.id)
            total_medidores += len(medidores)
            
            for medidor in medidores:
                lecturas = self._lectura_repo.get_by_medidor(medidor.id)
                total_lecturas += len(lecturas)
                
                for lectura in lecturas:
                    consumo_global += lectura.consumo_kwh
                    importe_global += lectura.importe_total
        
        return {
            "total_usuarios": total_usuarios,
            "usuarios_activos": usuarios_activos,
            "total_medidores": total_medidores,
            "total_lecturas": total_lecturas,
            "consumo_global": consumo_global,
            "importe_global": importe_global,
            "importe_global_redondeado": round(importe_global),
        }
