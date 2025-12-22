"""
Electric Tariffs App - Tests Unitarios para Algoritmos Críticos
===============================================================
Tests obligatorios según Plan de Construcción Etapa 2.
Validan cálculos matemáticos antes de implementar UI.

Ejecutar: python -m pytest tests/ -v
          python -m unittest tests.test_actions -v
"""

import unittest
from datetime import datetime, date, timedelta

from core.models import Tarifa, Lectura, Usuario, Medidor, RolUsuario, EstadoUsuario
from core.actions import (
    # Algoritmo 1: Cálculo por tramos
    calcular_importe,
    calcular_importe_redondeado,
    desglosar_consumo_por_tramos,
    # Algoritmo 2: Rollover
    detectar_rollover,
    calcular_consumo,
    ResultadoRollover,
    # Algoritmo 3: Efecto dominó
    recalcular_lecturas_afectadas,
    validar_lectura_retroactiva,
    # Validaciones
    validar_password,
    hash_password,
    verificar_password,
    autenticar_usuario,
    verificar_permiso_edicion_lectura,
    verificar_permiso_eliminacion_lectura,
    validar_tramos_tarifas,
    verificar_alerta_umbral,
)
from core.errors import (
    ContrasenaDebilError,
    CredencialesInvalidasError,
    UsuarioInactivoError,
    LecturaIncoherenteError,
    RolloverNoConfirmadoError,
    LecturaRetroactivaInvalidaError,
    PermisoDenegadoError,
    TiempoEdicionExpiradoError,
    TramosInvalidosError,
)
from core.config import MAX_MEDIDOR


# =============================================================================
# TARIFAS UNE DE PRUEBA (ERS 5.2)
# =============================================================================

def get_tarifas_une() -> list[Tarifa]:
    """Retorna las 10 tarifas UNE para testing."""
    return [
        Tarifa(id=1, limite_min=0, limite_max=100, precio_kwh=0.40),
        Tarifa(id=2, limite_min=100, limite_max=150, precio_kwh=1.30),
        Tarifa(id=3, limite_min=150, limite_max=200, precio_kwh=1.75),
        Tarifa(id=4, limite_min=200, limite_max=250, precio_kwh=3.00),
        Tarifa(id=5, limite_min=250, limite_max=300, precio_kwh=4.00),
        Tarifa(id=6, limite_min=300, limite_max=350, precio_kwh=7.50),
        Tarifa(id=7, limite_min=350, limite_max=400, precio_kwh=9.00),
        Tarifa(id=8, limite_min=400, limite_max=450, precio_kwh=10.00),
        Tarifa(id=9, limite_min=450, limite_max=500, precio_kwh=15.00),
        Tarifa(id=10, limite_min=500, limite_max=None, precio_kwh=25.00),
    ]


# =============================================================================
# TEST: CÁLCULO DE IMPORTE POR TRAMOS (ERS 6.1)
# =============================================================================

class TestCalculoImporte(unittest.TestCase):
    """Tests para el algoritmo de cálculo de importe por tramos."""
    
    def setUp(self):
        self.tarifas = get_tarifas_une()
    
    def test_consumo_cero(self):
        """Consumo 0 debe retornar importe 0."""
        resultado = calcular_importe(0, self.tarifas)
        self.assertEqual(resultado, 0.0)
    
    def test_consumo_negativo(self):
        """Consumo negativo debe retornar importe 0."""
        resultado = calcular_importe(-50, self.tarifas)
        self.assertEqual(resultado, 0.0)
    
    def test_consumo_primer_tramo_exacto(self):
        """100 kWh exactos = 100 × $0.40 = $40."""
        resultado = calcular_importe(100, self.tarifas)
        self.assertEqual(resultado, 40.0)
    
    def test_consumo_dos_tramos(self):
        """150 kWh = (100 × $0.40) + (50 × $1.30) = $40 + $65 = $105."""
        resultado = calcular_importe(150, self.tarifas)
        self.assertEqual(resultado, 105.0)
    
    def test_consumo_tres_tramos(self):
        """200 kWh = (100 × $0.40) + (50 × $1.30) + (50 × $1.75) = $40 + $65 + $87.50 = $192.50."""
        resultado = calcular_importe(200, self.tarifas)
        self.assertEqual(resultado, 192.5)
    
    def test_consumo_todos_tramos(self):
        """500 kWh debe consumir todos los tramos completos."""
        # Tramo 1: 100 × 0.40 = 40
        # Tramo 2: 50 × 1.30 = 65
        # Tramo 3: 50 × 1.75 = 87.5
        # Tramo 4: 50 × 3.00 = 150
        # Tramo 5: 50 × 4.00 = 200
        # Tramo 6: 50 × 7.50 = 375
        # Tramo 7: 50 × 9.00 = 450
        # Tramo 8: 50 × 10.00 = 500
        # Tramo 9: 50 × 15.00 = 750
        # Total: 2617.5
        resultado = calcular_importe(500, self.tarifas)
        self.assertEqual(resultado, 2617.5)
    
    def test_consumo_excede_todos_tramos(self):
        """550 kWh = todos los tramos + 50 kWh a $25 = $2617.5 + $1250 = $3867.5."""
        resultado = calcular_importe(550, self.tarifas)
        self.assertEqual(resultado, 3867.5)
    
    def test_consumo_muy_alto(self):
        """1000 kWh incluye 500 kWh en último tramo infinito."""
        # Tramos 1-9: 2617.5
        # Tramo 10: 500 × 25 = 12500
        # Total: 15117.5
        resultado = calcular_importe(1000, self.tarifas)
        self.assertEqual(resultado, 15117.5)
    
    def test_consumo_decimal(self):
        """125.5 kWh = (100 × $0.40) + (25.5 × $1.30) = $40 + $33.15 = $73.15."""
        resultado = calcular_importe(125.5, self.tarifas)
        self.assertAlmostEqual(resultado, 73.15, places=2)
    
    def test_tarifas_vacias(self):
        """Sin tarifas debe retornar 0."""
        resultado = calcular_importe(100, [])
        self.assertEqual(resultado, 0.0)
    
    def test_tarifas_desordenadas(self):
        """Las tarifas desordenadas deben ordenarse automáticamente."""
        tarifas_desordenadas = [
            Tarifa(id=2, limite_min=100, limite_max=150, precio_kwh=1.30),
            Tarifa(id=1, limite_min=0, limite_max=100, precio_kwh=0.40),
            Tarifa(id=3, limite_min=150, limite_max=None, precio_kwh=1.75),
        ]
        resultado = calcular_importe(175, tarifas_desordenadas)
        # 100 × 0.40 + 50 × 1.30 + 25 × 1.75 = 40 + 65 + 43.75 = 148.75
        self.assertEqual(resultado, 148.75)
    
    def test_importe_redondeado(self):
        """El importe redondeado debe ser entero CUP."""
        resultado = calcular_importe_redondeado(125.5, self.tarifas)
        self.assertEqual(resultado, 73)  # 73.15 → 73
        self.assertIsInstance(resultado, int)


class TestDesgloseTarifas(unittest.TestCase):
    """Tests para el desglose de consumo por tramos."""
    
    def setUp(self):
        self.tarifas = get_tarifas_une()
    
    def test_desglose_dos_tramos(self):
        """Desglose de 150 kWh debe mostrar 2 tramos."""
        desglose = desglosar_consumo_por_tramos(150, self.tarifas)
        self.assertEqual(len(desglose), 2)
        
        # Primer tramo: 100 kWh
        self.assertEqual(desglose[0]["consumo_tramo"], 100)
        self.assertEqual(desglose[0]["importe_tramo"], 40.0)
        
        # Segundo tramo: 50 kWh
        self.assertEqual(desglose[1]["consumo_tramo"], 50)
        self.assertEqual(desglose[1]["importe_tramo"], 65.0)
    
    def test_desglose_consumo_cero(self):
        """Consumo 0 debe retornar desglose vacío."""
        desglose = desglosar_consumo_por_tramos(0, self.tarifas)
        self.assertEqual(len(desglose), 0)


# =============================================================================
# TEST: DETECCIÓN DE ROLLOVER (ERS 6.2)
# =============================================================================

class TestDeteccionRollover(unittest.TestCase):
    """Tests para el algoritmo de detección de rollover."""
    
    def test_consumo_normal(self):
        """Lectura actual mayor que anterior = consumo normal."""
        resultado = detectar_rollover(1000.0, 1500.0)
        
        self.assertFalse(resultado.es_rollover)
        self.assertEqual(resultado.consumo, 500.0)
        self.assertFalse(resultado.requiere_confirmacion)
    
    def test_consumo_igual(self):
        """Lectura igual a anterior = consumo 0."""
        resultado = detectar_rollover(1000.0, 1000.0)
        
        self.assertFalse(resultado.es_rollover)
        self.assertEqual(resultado.consumo, 0.0)
    
    def test_rollover_detectado(self):
        """Rollover cuando anterior >= 95% de máximo y actual es pequeño."""
        # 99500 es > 95% de 99999.9 (que es 94999.905)
        resultado = detectar_rollover(99500.0, 150.0)
        
        self.assertTrue(resultado.es_rollover)
        # Consumo = (99999.9 - 99500) + 150 = 499.9 + 150 = 649.9
        self.assertAlmostEqual(resultado.consumo, 649.9, places=1)
        self.assertTrue(resultado.requiere_confirmacion)
    
    def test_rollover_limite_exacto(self):
        """Rollover en el límite exacto del umbral (95%)."""
        umbral = MAX_MEDIDOR * 0.95  # 94999.905
        resultado = detectar_rollover(umbral, 100.0)
        
        self.assertTrue(resultado.es_rollover)
    
    def test_error_lectura_menor_sin_rollover(self):
        """Lectura menor sin estar cerca del máximo = error."""
        # 50000 está lejos del máximo, no puede ser rollover
        resultado = detectar_rollover(50000.0, 40000.0)
        
        self.assertFalse(resultado.es_rollover)
        self.assertEqual(resultado.consumo, 0.0)
        self.assertTrue(resultado.requiere_confirmacion)
        self.assertIn("Error", resultado.mensaje)
    
    def test_calcular_consumo_normal(self):
        """calcular_consumo para caso normal."""
        consumo, es_rollover = calcular_consumo(1000.0, 1200.0)
        
        self.assertEqual(consumo, 200.0)
        self.assertFalse(es_rollover)
    
    def test_calcular_consumo_rollover_confirmado(self):
        """calcular_consumo con rollover confirmado."""
        consumo, es_rollover = calcular_consumo(99500.0, 150.0, confirmar_rollover=True)
        
        self.assertAlmostEqual(consumo, 649.9, places=1)
        self.assertTrue(es_rollover)
    
    def test_calcular_consumo_rollover_no_confirmado(self):
        """calcular_consumo con rollover sin confirmar debe lanzar excepción."""
        with self.assertRaises(RolloverNoConfirmadoError) as context:
            calcular_consumo(99500.0, 150.0, confirmar_rollover=False)
        
        self.assertAlmostEqual(context.exception.consumo_calculado, 649.9, places=1)
    
    def test_calcular_consumo_error_incoherente(self):
        """calcular_consumo con lectura incoherente debe lanzar excepción."""
        with self.assertRaises(LecturaIncoherenteError):
            calcular_consumo(50000.0, 40000.0)


# =============================================================================
# TEST: RECÁLCULO EN CASCADA - EFECTO DOMINÓ (ERS 6.3)
# =============================================================================

class TestEfectoDomino(unittest.TestCase):
    """Tests para el algoritmo de recálculo en cascada."""
    
    def setUp(self):
        self.tarifas = get_tarifas_une()
    
    def _crear_lectura(
        self,
        lectura_anterior: float,
        lectura_actual: float,
        fecha_fin: date
    ) -> Lectura:
        """Helper para crear lecturas de prueba."""
        consumo = lectura_actual - lectura_anterior
        return Lectura(
            id=1,
            medidor_id=1,
            autor_user_id=1,
            fecha_inicio=fecha_fin - timedelta(days=30),
            fecha_fin=fecha_fin,
            lectura_anterior=lectura_anterior,
            lectura_actual=lectura_actual,
            consumo_kwh=consumo,
            importe_total=calcular_importe(consumo, self.tarifas),
        )
    
    def test_recalculo_simple(self):
        """Recálculo actualiza lectura_anterior de siguiente registro."""
        lecturas = [
            self._crear_lectura(0, 100, date(2024, 1, 31)),
            self._crear_lectura(100, 200, date(2024, 2, 29)),  # Correcto
            self._crear_lectura(200, 350, date(2024, 3, 31)),  # Correcto
        ]
        
        # Simular edición: cambiar lectura_actual de enero a 120
        lecturas[0].lectura_actual = 120
        
        # Recalcular desde febrero (índice 1)
        modificadas = recalcular_lecturas_afectadas(lecturas, self.tarifas, desde_indice=1)
        
        # Febrero debe actualizarse: lectura_anterior = 120
        self.assertEqual(lecturas[1].lectura_anterior, 120)
        self.assertEqual(lecturas[1].consumo_kwh, 80)  # 200 - 120
        
        # Marzo debe mantenerse igual
        self.assertEqual(lecturas[2].lectura_anterior, 200)
    
    def test_recalculo_propagacion_completa(self):
        """El recálculo se propaga correctamente en cascada."""
        lecturas = [
            self._crear_lectura(0, 100, date(2024, 1, 31)),
            self._crear_lectura(100, 250, date(2024, 2, 29)),
            self._crear_lectura(250, 400, date(2024, 3, 31)),
        ]
        
        # Simular inserción retroactiva: nueva lectura en enero con valor 150
        lecturas[0].lectura_actual = 150
        
        # Recalcular todo desde febrero
        modificadas = recalcular_lecturas_afectadas(lecturas, self.tarifas, desde_indice=1)
        
        # Verificar propagación
        self.assertEqual(lecturas[1].lectura_anterior, 150)
        self.assertEqual(lecturas[1].consumo_kwh, 100)  # 250 - 150
        
        # Marzo no cambia su lectura_anterior (viene de febrero.lectura_actual=250)
        self.assertEqual(lecturas[2].lectura_anterior, 250)
    
    def test_recalculo_lista_vacia(self):
        """Recálculo con lista vacía no falla."""
        modificadas = recalcular_lecturas_afectadas([], self.tarifas, 0)
        self.assertEqual(len(modificadas), 0)


class TestValidacionRetroactiva(unittest.TestCase):
    """Tests para validación de lecturas retroactivas."""
    
    def test_lectura_retroactiva_valida(self):
        """Lectura retroactiva dentro de rango válido."""
        anterior = Lectura(lectura_actual=100, fecha_fin=date(2024, 1, 31))
        posterior = Lectura(lectura_actual=300, fecha_fin=date(2024, 3, 31))
        
        # 200 está entre 100 y 300, debe ser válido
        validar_lectura_retroactiva(200, date(2024, 2, 29), anterior, posterior)
    
    def test_lectura_retroactiva_menor_que_anterior(self):
        """Lectura retroactiva menor que anterior debe fallar."""
        anterior = Lectura(lectura_actual=100, fecha_fin=date(2024, 1, 31))
        
        with self.assertRaises(LecturaRetroactivaInvalidaError):
            validar_lectura_retroactiva(50, date(2024, 2, 29), anterior, None)
    
    def test_lectura_retroactiva_mayor_que_posterior(self):
        """Lectura retroactiva mayor que posterior debe fallar."""
        posterior = Lectura(lectura_actual=300, fecha_fin=date(2024, 3, 31))
        
        with self.assertRaises(LecturaRetroactivaInvalidaError):
            validar_lectura_retroactiva(350, date(2024, 2, 29), None, posterior)
    
    def test_lectura_retroactiva_sin_contexto(self):
        """Lectura retroactiva sin anterior ni posterior es válida."""
        # No debe lanzar excepción
        validar_lectura_retroactiva(500, date(2024, 2, 29), None, None)


# =============================================================================
# TEST: VALIDACIÓN DE CONTRASEÑA (RF-08)
# =============================================================================

class TestValidacionPassword(unittest.TestCase):
    """Tests para validación de contraseña."""
    
    def test_password_valida(self):
        """Contraseña válida: 6+ chars y 1 número."""
        self.assertTrue(validar_password("abc123"))
        self.assertTrue(validar_password("password1"))
        self.assertTrue(validar_password("1abcdef"))
    
    def test_password_corta(self):
        """Contraseña menor a 6 caracteres debe fallar."""
        with self.assertRaises(ContrasenaDebilError):
            validar_password("abc1")
    
    def test_password_sin_numero(self):
        """Contraseña sin número debe fallar."""
        with self.assertRaises(ContrasenaDebilError):
            validar_password("abcdefgh")
    
    def test_hash_y_verificacion(self):
        """El hash y verificación deben funcionar correctamente."""
        password = "miPassword123"
        hash_resultado = hash_password(password)
        
        # Hash debe ser diferente al original
        self.assertNotEqual(password, hash_resultado)
        
        # Verificación debe funcionar
        self.assertTrue(verificar_password(password, hash_resultado))
        self.assertFalse(verificar_password("otraPassword", hash_resultado))


# =============================================================================
# TEST: AUTENTICACIÓN (RF-05)
# =============================================================================

class TestAutenticacion(unittest.TestCase):
    """Tests para autenticación de usuarios."""
    
    def test_autenticacion_exitosa(self):
        """Autenticación exitosa con credenciales correctas."""
        password_hash = hash_password("admin123")
        usuario = Usuario(
            id=1,
            username="admin",
            password_hash=password_hash,
            estado=EstadoUsuario.ACTIVO,
        )
        
        resultado = autenticar_usuario(usuario, "admin123")
        self.assertEqual(resultado.id, 1)
    
    def test_autenticacion_usuario_none(self):
        """Autenticación con usuario inexistente debe fallar."""
        with self.assertRaises(CredencialesInvalidasError):
            autenticar_usuario(None, "password")
    
    def test_autenticacion_password_incorrecta(self):
        """Autenticación con contraseña incorrecta debe fallar."""
        password_hash = hash_password("correcta")
        usuario = Usuario(
            id=1,
            username="test",
            password_hash=password_hash,
            estado=EstadoUsuario.ACTIVO,
        )
        
        with self.assertRaises(CredencialesInvalidasError):
            autenticar_usuario(usuario, "incorrecta")
    
    def test_autenticacion_usuario_inactivo(self):
        """Autenticación de usuario inactivo debe fallar."""
        password_hash = hash_password("password123")
        usuario = Usuario(
            id=1,
            username="test",
            password_hash=password_hash,
            estado=EstadoUsuario.INACTIVO,
        )
        
        with self.assertRaises(UsuarioInactivoError):
            autenticar_usuario(usuario, "password123")


# =============================================================================
# TEST: PERMISOS DE EDICIÓN (RF-31 a RF-37)
# =============================================================================

class TestPermisosEdicion(unittest.TestCase):
    """Tests para permisos de edición de lecturas."""
    
    def setUp(self):
        self.admin = Usuario(id=1, rol=RolUsuario.ADMIN)
        self.propietario = Usuario(id=2, rol=RolUsuario.USER)
        self.vinculado = Usuario(id=3, rol=RolUsuario.USER)
        self.medidor = Medidor(id=1, propietario_id=2, etiqueta="Casa")
    
    def test_admin_puede_editar_cualquier_lectura(self):
        """Admin puede editar cualquier lectura."""
        lectura = Lectura(id=1, autor_user_id=3, created_at=datetime.now())
        
        # No debe lanzar excepción
        verificar_permiso_edicion_lectura(
            self.admin, lectura, self.medidor, es_propietario=False
        )
    
    def test_propietario_puede_editar_cualquier_lectura(self):
        """Propietario puede editar cualquier lectura de su medidor."""
        lectura = Lectura(id=1, autor_user_id=3, created_at=datetime.now())
        
        # No debe lanzar excepción
        verificar_permiso_edicion_lectura(
            self.propietario, lectura, self.medidor, es_propietario=True
        )
    
    def test_vinculado_puede_editar_propia_dentro_48h(self):
        """Vinculado puede editar su propia lectura dentro de 48h."""
        lectura = Lectura(
            id=1,
            autor_user_id=3,
            created_at=datetime.now() - timedelta(hours=24)  # Hace 24h
        )
        
        # No debe lanzar excepción
        verificar_permiso_edicion_lectura(
            self.vinculado, lectura, self.medidor, es_propietario=False
        )
    
    def test_vinculado_no_puede_editar_lectura_ajena(self):
        """Vinculado no puede editar lectura de otro usuario."""
        lectura = Lectura(id=1, autor_user_id=2, created_at=datetime.now())
        
        with self.assertRaises(PermisoDenegadoError):
            verificar_permiso_edicion_lectura(
                self.vinculado, lectura, self.medidor, es_propietario=False
            )
    
    def test_vinculado_no_puede_editar_despues_48h(self):
        """Vinculado no puede editar después de 48 horas."""
        lectura = Lectura(
            id=1,
            autor_user_id=3,
            created_at=datetime.now() - timedelta(hours=50)  # Hace 50h
        )
        
        with self.assertRaises(TiempoEdicionExpiradoError):
            verificar_permiso_edicion_lectura(
                self.vinculado, lectura, self.medidor, es_propietario=False
            )


class TestPermisosEliminacion(unittest.TestCase):
    """Tests para permisos de eliminación de lecturas."""
    
    def setUp(self):
        self.admin = Usuario(id=1, rol=RolUsuario.ADMIN)
        self.propietario = Usuario(id=2, rol=RolUsuario.USER)
        self.vinculado = Usuario(id=3, rol=RolUsuario.USER)
        self.medidor = Medidor(id=1, propietario_id=2, etiqueta="Casa")
    
    def test_admin_puede_eliminar(self):
        """Admin puede eliminar lecturas."""
        verificar_permiso_eliminacion_lectura(
            self.admin, self.medidor, es_propietario=False
        )
    
    def test_propietario_puede_eliminar(self):
        """Propietario puede eliminar lecturas de su medidor."""
        verificar_permiso_eliminacion_lectura(
            self.propietario, self.medidor, es_propietario=True
        )
    
    def test_vinculado_no_puede_eliminar(self):
        """Vinculado NO puede eliminar lecturas (RF-36)."""
        with self.assertRaises(PermisoDenegadoError):
            verificar_permiso_eliminacion_lectura(
                self.vinculado, self.medidor, es_propietario=False
            )


# =============================================================================
# TEST: VALIDACIÓN DE TARIFAS (RF-43)
# =============================================================================

class TestValidacionTarifas(unittest.TestCase):
    """Tests para validación de tramos de tarifas."""
    
    def test_tarifas_validas(self):
        """Tarifas UNE válidas no lanzan excepción."""
        tarifas = get_tarifas_une()
        validar_tramos_tarifas(tarifas)  # No debe lanzar
    
    def test_tarifas_vacias(self):
        """Lista vacía de tarifas debe fallar."""
        with self.assertRaises(TramosInvalidosError):
            validar_tramos_tarifas([])
    
    def test_primer_tramo_no_empieza_en_cero(self):
        """Primer tramo debe empezar en 0."""
        tarifas = [
            Tarifa(limite_min=50, limite_max=100, precio_kwh=1.0),
            Tarifa(limite_min=100, limite_max=None, precio_kwh=2.0),
        ]
        
        with self.assertRaises(TramosInvalidosError):
            validar_tramos_tarifas(tarifas)
    
    def test_gap_entre_tramos(self):
        """Gap entre tramos debe fallar."""
        tarifas = [
            Tarifa(limite_min=0, limite_max=100, precio_kwh=1.0),
            Tarifa(limite_min=150, limite_max=None, precio_kwh=2.0),  # Gap: 100-150
        ]
        
        with self.assertRaises(TramosInvalidosError):
            validar_tramos_tarifas(tarifas)
    
    def test_ultimo_tramo_no_infinito(self):
        """Último tramo debe ser infinito."""
        tarifas = [
            Tarifa(limite_min=0, limite_max=100, precio_kwh=1.0),
            Tarifa(limite_min=100, limite_max=200, precio_kwh=2.0),  # No infinito
        ]
        
        with self.assertRaises(TramosInvalidosError):
            validar_tramos_tarifas(tarifas)


# =============================================================================
# TEST: ALERTAS DE UMBRAL (RF-52)
# =============================================================================

class TestAlertaUmbral(unittest.TestCase):
    """Tests para verificación de alertas de umbral."""
    
    def test_consumo_bajo_umbral(self):
        """Consumo bajo umbral no genera alerta."""
        self.assertFalse(verificar_alerta_umbral(100, 200))
    
    def test_consumo_igual_umbral(self):
        """Consumo igual a umbral genera alerta."""
        self.assertTrue(verificar_alerta_umbral(200, 200))
    
    def test_consumo_sobre_umbral(self):
        """Consumo sobre umbral genera alerta."""
        self.assertTrue(verificar_alerta_umbral(250, 200))
    
    def test_umbral_none(self):
        """Sin umbral configurado no genera alerta."""
        self.assertFalse(verificar_alerta_umbral(1000, None))


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
