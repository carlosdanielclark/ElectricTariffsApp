"""
Electric Tariffs App - Vistas Flet
==================================
Funciones que crean componentes visuales de la interfaz.
Compatibles con Flet 0.28+
"""

from ui.views.login_view import create_login_view, LoginView
from ui.views.registro_view import create_registro_view, RegistroView
from ui.views.cambiar_password_view import create_cambiar_password_view, CambiarPasswordView
from ui.views.medidores_view import create_medidores_view, MedidoresView
from ui.views.lecturas_view import create_lecturas_view
from ui.views.dashboard_view import create_dashboard_view

__all__ = [
    "create_login_view",
    "create_registro_view",
    "create_cambiar_password_view",
    "create_medidores_view",
    "create_lecturas_view",
    "create_dashboard_view",
    # Alias para compatibilidad
    "LoginView",
    "RegistroView",
    "CambiarPasswordView",
    "MedidoresView",
]
