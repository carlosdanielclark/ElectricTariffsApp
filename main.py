"""
Electric Tariffs App - Punto de Entrada
========================================
Inicializa base de datos y servicios ANTES de cargar la UI.
Según agent.md: La creación de tablas debe asegurarse en el arranque
antes de cargar cualquier UI para evitar OperationalError.
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz está en el path
ROOT_DIR = Path(__file__).parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> None:
    """
    Función principal de la aplicación.
    Orden de inicialización:
    1. Base de datos (tablas + admin + tarifas + recovery key)
    2. Sistema de logs
    3. Interfaz de usuario Flet
    """
    # =========================================================================
    # PASO 1: Inicializar Base de Datos
    # =========================================================================
    print("Inicializando base de datos...")
    from data.database import init_db
    init_db()
    print("✓ Base de datos lista")
    
    # =========================================================================
    # PASO 2: Inicializar Sistema de Logs
    # =========================================================================
    print("Inicializando sistema de logs...")
    from data.logger import get_logger
    logger = get_logger()
    print("✓ Sistema de logs listo")
    
    # =========================================================================
    # PASO 3: Verificar Integridad de Datos Críticos
    # =========================================================================
    print("Verificando datos críticos...")
    from data.repositories import UsuarioRepository, TarifaRepository
    
    usuario_repo = UsuarioRepository()
    tarifa_repo = TarifaRepository()
    
    # Verificar que existe admin
    admin = usuario_repo.get_by_username("admin")
    if admin is None:
        print("⚠ ADVERTENCIA: Usuario admin no encontrado. Recreando...")
        from data.database import get_db
        db = get_db()
        db.initialize_database()
    else:
        print(f"✓ Admin encontrado: {admin.nombre}")
    
    # Verificar que existen tarifas
    tarifas = tarifa_repo.get_all()
    if len(tarifas) == 0:
        print("⚠ ADVERTENCIA: Tarifas no encontradas. Recreando...")
        from data.database import get_db
        db = get_db()
        db.initialize_database()
    else:
        print(f"✓ Tarifas cargadas: {len(tarifas)} tramos")
    
    # =========================================================================
    # PASO 4: Verificar Recovery Key
    # =========================================================================
    from core.config import RECOVERY_KEY_PATH
    if RECOVERY_KEY_PATH.exists():
        print("✓ Recovery key presente")
    else:
        print("⚠ Recovery key no encontrada")
    
    # =========================================================================
    # PASO 5: Lanzar Interfaz de Usuario
    # =========================================================================
    print("\n" + "=" * 50)
    print("Electric Tariffs App v4.0")
    print("=" * 50)
    print("Iniciando interfaz de usuario...\n")
    
    from ui.app import run_app
    run_app()


if __name__ == "__main__":
    main()
