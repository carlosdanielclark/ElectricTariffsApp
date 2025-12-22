"""
Electric Tariffs App - Casos de Uso (Actions)
=============================================
Lógica de negocio pura. NUNCA importar flet o sqlite3.
Implementa algoritmos críticos según ERS sección 6.

Algoritmos:
- Cálculo de importe por tramos (ERS 6.1)
- Detección de rollover (ERS 6.2)
- Recálculo en cascada - Efecto Dominó (ERS 6.3)
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional

import bcrypt

from core.config import (
    MAX_MEDIDOR,
    UMBRAL_ROLLOVER,
    BCRYPT_ROUNDS,
    MIN_PASSWORD_LENGTH,
    VINCULADO_EDIT_HOURS,
)
from core.models import (
    Usuario,
    Medidor,
    Lectura,
    Tarifa,
    RolUsuario,
    EstadoUsuario,
)
from core.errors import (
    ContrasenaDebilError,
    CredencialesInvalidasError,
    UsuarioInactivoError,
    LecturaIncoherenteError,
    LecturaRetroactivaInvalidaError,
    RolloverNoConfirmadoError,
    PermisoDenegadoError,
    TiempoEdicionExpiradoError,
    FechaFuturaError,
    TramosInvalidosError,
)


# =============================================================================
# ALGORITMO 1: CÁLCULO DE IMPORTE POR TRAMOS (ERS 6.1)
# =============================================================================

def calcular_importe(consumo_total: float, tarifas: list[Tarifa]) -> float:
    """
    Calcula el importe total aplicando tarifas escalonadas.
    
    Según ERS 6.1:
    - Recorre los tramos de menor a mayor
    - Aplica el precio de cada tramo al rango correspondiente
    - El último tramo (limite_max=None) aplica a todo el restante
    
    Args:
        consumo_total: Consumo en kWh a facturar
        tarifas: Lista de tarifas ordenadas por limite_min
        
    Returns:
        Importe total con precisión completa (float)
        Para UI usar round() -> CUP enteros (RF-39)
    
    Example:
        >>> tarifas = [Tarifa(limite_min=0, limite_max=100, precio_kwh=0.40), ...]
        >>> calcular_importe(150, tarifas)
        105.0  # (100 * 0.40) + (50 * 1.30)
    """
    if consumo_total <= 0:
        return 0.0
    
    if not tarifas:
        return 0.0
    
    # Ordenar tarifas por limite_min (por seguridad)
    tarifas_ordenadas = sorted(tarifas, key=lambda t: t.limite_min)
    
    restante = consumo_total
    total = 0.0
    
    for tarifa in tarifas_ordenadas:
        if restante <= 0:
            break
            
        # Último tramo (infinito)
        if tarifa.limite_max is None:
            total += restante * tarifa.precio_kwh
            break
        
        # Calcular rango del tramo
        rango = tarifa.limite_max - tarifa.limite_min
        
        if restante > rango:
            # Consumo excede este tramo
            total += rango * tarifa.precio_kwh
            restante -= rango
        else:
            # Consumo se agota en este tramo
            total += restante * tarifa.precio_kwh
            break
    
    return total


def calcular_importe_redondeado(consumo_total: float, tarifas: list[Tarifa]) -> int:
    """
    Calcula importe y redondea a CUP enteros para presentación (RF-39).
    """
    return round(calcular_importe(consumo_total, tarifas))


def desglosar_consumo_por_tramos(
    consumo_total: float, 
    tarifas: list[Tarifa]
) -> list[dict[str, float]]:
    """
    Desglosa el consumo mostrando cuánto se consume en cada tramo.
    Útil para mostrar detalle de factura.
    
    Returns:
        Lista de dicts con: tramo_id, limite_min, limite_max, consumo_tramo, 
                           precio_kwh, importe_tramo
    """
    if consumo_total <= 0 or not tarifas:
        return []
    
    tarifas_ordenadas = sorted(tarifas, key=lambda t: t.limite_min)
    restante = consumo_total
    desglose = []
    
    for tarifa in tarifas_ordenadas:
        if restante <= 0:
            break
        
        if tarifa.limite_max is None:
            consumo_tramo = restante
        else:
            rango = tarifa.limite_max - tarifa.limite_min
            consumo_tramo = min(restante, rango)
        
        importe_tramo = consumo_tramo * tarifa.precio_kwh
        
        desglose.append({
            "tramo_id": tarifa.id,
            "limite_min": tarifa.limite_min,
            "limite_max": tarifa.limite_max,
            "consumo_tramo": consumo_tramo,
            "precio_kwh": tarifa.precio_kwh,
            "importe_tramo": importe_tramo,
        })
        
        restante -= consumo_tramo
    
    return desglose


# =============================================================================
# ALGORITMO 2: DETECCIÓN DE ROLLOVER (ERS 6.2)
# =============================================================================

class ResultadoRollover:
    """Resultado del análisis de rollover."""
    
    def __init__(
        self,
        es_rollover: bool,
        consumo: float,
        requiere_confirmacion: bool = False,
        mensaje: str = ""
    ):
        self.es_rollover = es_rollover
        self.consumo = consumo
        self.requiere_confirmacion = requiere_confirmacion
        self.mensaje = mensaje


def detectar_rollover(
    lectura_anterior: float,
    lectura_actual: float,
    max_medidor: float = MAX_MEDIDOR,
    umbral_rollover: float = UMBRAL_ROLLOVER
) -> ResultadoRollover:
    """
    Detecta automáticamente reset del medidor (rollover).
    
    Según ERS 6.2 (RF-22 a RF-25):
    - Si lectura_actual >= lectura_anterior: consumo normal
    - Si lectura_anterior >= 95% del máximo Y lectura_actual es pequeña: rollover
    - Otros casos: error o requiere confirmación manual
    
    Args:
        lectura_anterior: Lectura del período anterior
        lectura_actual: Lectura actual del medidor
        max_medidor: Valor máximo del medidor (default 99999.9)
        umbral_rollover: Porcentaje del máximo para considerar rollover (default 0.95)
    
    Returns:
        ResultadoRollover con: es_rollover, consumo, requiere_confirmacion, mensaje
    
    Example:
        >>> detectar_rollover(99500.0, 150.0)
        ResultadoRollover(es_rollover=True, consumo=649.9, ...)
    """
    # Caso normal: lectura actual mayor o igual a anterior
    if lectura_actual >= lectura_anterior:
        consumo = lectura_actual - lectura_anterior
        return ResultadoRollover(
            es_rollover=False,
            consumo=consumo,
            requiere_confirmacion=False,
            mensaje="Consumo normal"
        )
    
    # Lectura actual menor que anterior - posible rollover
    umbral_valor = max_medidor * umbral_rollover
    
    if lectura_anterior >= umbral_valor:
        # Rollover detectado (RF-24)
        consumo = (max_medidor - lectura_anterior) + lectura_actual
        return ResultadoRollover(
            es_rollover=True,
            consumo=consumo,
            requiere_confirmacion=True,
            mensaje=f"Se detectó reinicio del medidor. Consumo calculado: {consumo:.1f} kWh"
        )
    
    # Caso anómalo: lectura menor sin estar cerca del máximo
    # Esto es un error de entrada (RF-22)
    return ResultadoRollover(
        es_rollover=False,
        consumo=0.0,
        requiere_confirmacion=True,
        mensaje=f"Error: Lectura actual ({lectura_actual}) menor que anterior ({lectura_anterior})"
    )


def calcular_consumo(
    lectura_anterior: float,
    lectura_actual: float,
    confirmar_rollover: bool = False
) -> tuple[float, bool]:
    """
    Calcula el consumo entre dos lecturas.
    
    Args:
        lectura_anterior: Lectura del período anterior
        lectura_actual: Lectura actual
        confirmar_rollover: Si True, acepta rollover sin error
        
    Returns:
        Tupla (consumo, es_rollover)
        
    Raises:
        LecturaIncoherenteError: Si lectura es incoherente y no hay rollover
        RolloverNoConfirmadoError: Si hay rollover pero no se confirmó
    """
    resultado = detectar_rollover(lectura_anterior, lectura_actual)
    
    if resultado.es_rollover:
        if not confirmar_rollover and resultado.requiere_confirmacion:
            raise RolloverNoConfirmadoError(resultado.consumo)
        return resultado.consumo, True
    
    if resultado.consumo == 0.0 and resultado.requiere_confirmacion:
        # Error de coherencia
        raise LecturaIncoherenteError(lectura_anterior, lectura_actual)
    
    return resultado.consumo, False


# =============================================================================
# ALGORITMO 3: RECÁLCULO EN CASCADA - EFECTO DOMINÓ (ERS 6.3)
# =============================================================================

def recalcular_lecturas_afectadas(
    lecturas: list[Lectura],
    tarifas: list[Tarifa],
    desde_indice: int = 0
) -> list[Lectura]:
    """
    Recalcula consumos e importes de lecturas afectadas por edición/inserción.
    
    Según ERS 6.3 (RF-33, RF-34):
    - Cada lectura obtiene su lectura_anterior de la lectura previa cronológica
    - Recalcula consumo_kwh = lectura_actual - lectura_anterior
    - Recalcula importe_total con tarifas actuales
    
    IMPORTANTE: Las lecturas DEBEN estar ordenadas por fecha_fin.
    
    Args:
        lecturas: Lista de lecturas ordenadas cronológicamente
        tarifas: Tarifas para calcular importes
        desde_indice: Índice desde donde empezar a recalcular
        
    Returns:
        Lista de lecturas modificadas (mismas instancias, mutadas)
    """
    if not lecturas or desde_indice >= len(lecturas):
        return []
    
    lecturas_modificadas = []
    
    for i in range(desde_indice, len(lecturas)):
        lectura = lecturas[i]
        modificada = False
        
        if i == 0:
            # Primera lectura: no tiene anterior, mantener valores
            continue
        
        lectura_previa = lecturas[i - 1]
        
        # Actualizar lectura_anterior si difiere
        if lectura.lectura_anterior != lectura_previa.lectura_actual:
            lectura.lectura_anterior = lectura_previa.lectura_actual
            modificada = True
        
        # Recalcular consumo
        try:
            nuevo_consumo, es_rollover = calcular_consumo(
                lectura.lectura_anterior,
                lectura.lectura_actual,
                confirmar_rollover=lectura.es_rollover  # Mantener flag existente
            )
            
            if abs(lectura.consumo_kwh - nuevo_consumo) > 0.01:
                lectura.consumo_kwh = nuevo_consumo
                lectura.es_rollover = es_rollover
                modificada = True
                
        except (LecturaIncoherenteError, RolloverNoConfirmadoError):
            # Mantener valores existentes si hay error
            pass
        
        # Recalcular importe
        nuevo_importe = calcular_importe(lectura.consumo_kwh, tarifas)
        if abs(lectura.importe_total - nuevo_importe) > 0.01:
            lectura.importe_total = nuevo_importe
            modificada = True
        
        if modificada:
            lectura.updated_at = datetime.now()
            lecturas_modificadas.append(lectura)
    
    return lecturas_modificadas


def validar_lectura_retroactiva(
    nueva_lectura: float,
    fecha_nueva: date,
    lectura_anterior: Optional[Lectura],
    lectura_posterior: Optional[Lectura]
) -> None:
    """
    Valida que una lectura retroactiva sea coherente (RF-30).
    
    La lectura retroactiva debe ser:
    - Mayor que la lectura anterior cronológica
    - Menor que la lectura posterior cronológica
    
    Args:
        nueva_lectura: Valor de la nueva lectura
        fecha_nueva: Fecha de la nueva lectura
        lectura_anterior: Lectura cronológicamente anterior (puede ser None)
        lectura_posterior: Lectura cronológicamente posterior (puede ser None)
        
    Raises:
        LecturaRetroactivaInvalidaError: Si la lectura no es coherente
    """
    if lectura_anterior is not None:
        if nueva_lectura < lectura_anterior.lectura_actual:
            # Verificar si podría ser rollover
            resultado = detectar_rollover(
                lectura_anterior.lectura_actual, 
                nueva_lectura
            )
            if not resultado.es_rollover:
                raise LecturaRetroactivaInvalidaError(
                    f"La lectura ({nueva_lectura}) debe ser mayor que la anterior "
                    f"({lectura_anterior.lectura_actual} del {lectura_anterior.fecha_fin})"
                )
    
    if lectura_posterior is not None:
        if nueva_lectura > lectura_posterior.lectura_actual:
            raise LecturaRetroactivaInvalidaError(
                f"La lectura ({nueva_lectura}) debe ser menor que la posterior "
                f"({lectura_posterior.lectura_actual} del {lectura_posterior.fecha_fin})"
            )


# =============================================================================
# VALIDACIÓN DE CONTRASEÑA (RF-08)
# =============================================================================

def validar_password(password: str) -> bool:
    """
    Valida que la contraseña cumpla requisitos mínimos (RF-08).
    
    Requisitos:
    - Mínimo 6 caracteres
    - Al menos 1 número
    
    Args:
        password: Contraseña a validar
        
    Returns:
        True si cumple requisitos
        
    Raises:
        ContrasenaDebilError: Si no cumple requisitos
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ContrasenaDebilError(
            f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"
        )
    
    if not re.search(r'\d', password):
        raise ContrasenaDebilError(
            "La contraseña debe contener al menos 1 número"
        )
    
    return True


def hash_password(password: str) -> str:
    """
    Genera hash bcrypt de contraseña (RNF-06).
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash bcrypt como string
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(BCRYPT_ROUNDS)
    ).decode("utf-8")


def verificar_password(password: str, password_hash: str) -> bool:
    """
    Verifica contraseña contra hash almacenado.
    
    Args:
        password: Contraseña en texto plano
        password_hash: Hash bcrypt almacenado
        
    Returns:
        True si coincide
    """
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


# =============================================================================
# AUTENTICACIÓN (RF-05)
# =============================================================================

def autenticar_usuario(
    usuario: Optional[Usuario],
    password: str
) -> Usuario:
    """
    Autentica usuario verificando contraseña y estado.
    
    Args:
        usuario: Usuario obtenido de BD (puede ser None si no existe)
        password: Contraseña proporcionada
        
    Returns:
        Usuario autenticado
        
    Raises:
        CredencialesInvalidasError: Si usuario no existe o contraseña incorrecta
        UsuarioInactivoError: Si usuario está desactivado
    """
    if usuario is None:
        raise CredencialesInvalidasError()
    
    if not verificar_password(password, usuario.password_hash):
        raise CredencialesInvalidasError()
    
    if usuario.estado == EstadoUsuario.INACTIVO:
        raise UsuarioInactivoError()
    
    return usuario


# =============================================================================
# PERMISOS DE EDICIÓN (RF-31 a RF-37)
# =============================================================================

def verificar_permiso_edicion_lectura(
    usuario: Usuario,
    lectura: Lectura,
    medidor: Medidor,
    es_propietario: bool
) -> None:
    """
    Verifica si usuario puede editar una lectura (RF-31 a RF-33).
    
    Reglas:
    - Propietario: puede editar CUALQUIER lectura de su medidor
    - Vinculado: solo sus propias lecturas dentro de 48 horas
    
    Args:
        usuario: Usuario que intenta editar
        lectura: Lectura a editar
        medidor: Medidor asociado
        es_propietario: Si usuario es propietario del medidor
        
    Raises:
        PermisoDenegadoError: Si no tiene permisos
        TiempoEdicionExpiradoError: Si vinculado excede 48h
    """
    # Admin siempre puede
    if usuario.es_admin:
        return
    
    # Propietario puede editar cualquier lectura de su medidor (RF-31)
    if es_propietario:
        return
    
    # Vinculado: verificar autoría (RF-32)
    if lectura.autor_user_id != usuario.id:
        raise PermisoDenegadoError(
            "Solo puedes editar las lecturas que tú registraste"
        )
    
    # Vinculado: verificar tiempo (RF-32 - 48 horas)
    if lectura.created_at:
        tiempo_transcurrido = datetime.now() - lectura.created_at
        limite = timedelta(hours=VINCULADO_EDIT_HOURS)
        
        if tiempo_transcurrido > limite:
            raise TiempoEdicionExpiradoError(VINCULADO_EDIT_HOURS)


def verificar_permiso_eliminacion_lectura(
    usuario: Usuario,
    medidor: Medidor,
    es_propietario: bool
) -> None:
    """
    Verifica si usuario puede eliminar lecturas (RF-35 a RF-37).
    
    Reglas:
    - Solo propietario puede eliminar lecturas
    - Vinculados NO pueden eliminar (ni siquiera las propias)
    
    Args:
        usuario: Usuario que intenta eliminar
        medidor: Medidor asociado
        es_propietario: Si usuario es propietario del medidor
        
    Raises:
        PermisoDenegadoError: Si no tiene permisos
    """
    # Admin siempre puede
    if usuario.es_admin:
        return
    
    # Solo propietario puede eliminar (RF-35)
    if not es_propietario:
        raise PermisoDenegadoError(
            "Solo el propietario del medidor puede eliminar lecturas. "
            "Para correcciones, registra una lectura correctiva."
        )


# =============================================================================
# VALIDACIÓN DE FECHAS
# =============================================================================

def validar_fecha_no_futura(fecha: date) -> None:
    """
    Valida que la fecha no sea futura.
    
    Args:
        fecha: Fecha a validar
        
    Raises:
        FechaFuturaError: Si la fecha es futura
    """
    if fecha > date.today():
        raise FechaFuturaError(f"La fecha {fecha} no puede ser futura")


def validar_periodo(fecha_inicio: date, fecha_fin: date) -> None:
    """
    Valida que el período sea válido.
    
    Args:
        fecha_inicio: Fecha de inicio del período
        fecha_fin: Fecha de fin del período
        
    Raises:
        ValueError: Si fecha_inicio > fecha_fin
        FechaFuturaError: Si fecha_fin es futura
    """
    if fecha_inicio > fecha_fin:
        raise ValueError("La fecha de inicio no puede ser posterior a la fecha de fin")
    
    validar_fecha_no_futura(fecha_fin)


# =============================================================================
# VALIDACIÓN DE TARIFAS (RF-43)
# =============================================================================

def validar_tramos_tarifas(tarifas: list[Tarifa]) -> None:
    """
    Valida que los tramos de tarifa sean consecutivos sin solapamiento (RF-43).
    
    Args:
        tarifas: Lista de tarifas a validar
        
    Raises:
        TramosInvalidosError: Si hay solapamiento o gaps
    """
    if not tarifas:
        raise TramosInvalidosError("Debe existir al menos un tramo de tarifa")
    
    # Ordenar por limite_min
    tarifas_ordenadas = sorted(tarifas, key=lambda t: t.limite_min)
    
    # Verificar que el primer tramo empiece en 0
    if tarifas_ordenadas[0].limite_min != 0:
        raise TramosInvalidosError("El primer tramo debe empezar en 0 kWh")
    
    # Verificar consecutividad
    for i in range(len(tarifas_ordenadas) - 1):
        actual = tarifas_ordenadas[i]
        siguiente = tarifas_ordenadas[i + 1]
        
        if actual.limite_max is None:
            raise TramosInvalidosError(
                "Solo el último tramo puede tener límite máximo infinito"
            )
        
        if actual.limite_max != siguiente.limite_min:
            raise TramosInvalidosError(
                f"Gap o solapamiento entre tramos: {actual.limite_max} != {siguiente.limite_min}"
            )
    
    # Verificar que el último tramo sea infinito
    if tarifas_ordenadas[-1].limite_max is not None:
        raise TramosInvalidosError(
            "El último tramo debe tener límite máximo infinito (NULL)"
        )


# =============================================================================
# CÁLCULOS DE DASHBOARD
# =============================================================================

def calcular_promedio_diario(consumo_mes: float, dias_mes: int = 30) -> float:
    """
    Calcula promedio diario de consumo.
    
    Args:
        consumo_mes: Consumo total del mes en kWh
        dias_mes: Días del mes (default 30)
        
    Returns:
        Promedio diario en kWh
    """
    if dias_mes <= 0:
        return 0.0
    return consumo_mes / dias_mes


def verificar_alerta_umbral(consumo: float, umbral: Optional[float]) -> bool:
    """
    Verifica si el consumo supera el umbral de alerta (RF-52).
    
    Args:
        consumo: Consumo actual en kWh
        umbral: Umbral configurado (puede ser None si no hay alerta)
        
    Returns:
        True si consumo >= umbral
    """
    if umbral is None:
        return False
    return consumo >= umbral
