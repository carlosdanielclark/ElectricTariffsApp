"""
Electric Tariffs App - Vista de Login
=====================================
Pantalla de inicio de sesión con Flet.
Implementa RF-05 (Login), RF-09 (Bloqueo), RF-10 (Recuperación).
"""

import flet as ft
from typing import Callable, Optional

from ui.styles import (
    Colors, Sizes, 
    get_input_style, get_button_style, get_card_style,
    show_snackbar, create_loading_indicator,
)
from ui.viewmodels.auth_viewmodel import AuthViewModel


def create_login_view(
    page: ft.Page,
    on_login_success: Callable,
    on_registro: Callable,
    on_cambiar_password: Callable,
    is_dark: bool = True
) -> ft.Container:
    """
    Crea la vista de login.
    
    Args:
        page: Página Flet
        on_login_success: Callback cuando login exitoso
        on_registro: Callback para ir a registro
        on_cambiar_password: Callback para cambio obligatorio de password
        is_dark: Si usar tema oscuro
        
    Returns:
        Container con la vista de login
    """
    viewmodel = AuthViewModel()
    
    # Controles
    txt_usuario = ft.TextField(
        label="Usuario",
        prefix_icon=ft.Icons.PERSON,
        **get_input_style(is_dark),
    )
    
    txt_password = ft.TextField(
        label="Contraseña",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        **get_input_style(is_dark),
    )
    
    error_text = ft.Text(
        "",
        color=Colors.ERROR,
        size=14,
        text_align=ft.TextAlign.CENTER,
    )
    
    loading = create_loading_indicator()
    loading.visible = False
    
    btn_login = ft.ElevatedButton(
        text="Iniciar Sesión",
        width=320,
        **get_button_style(is_primary=True),
    )
    
    # =========================================================================
    # HANDLERS - Definidos como funciones para evitar problemas con lambdas
    # =========================================================================
    
    def handle_login(e):
        """Handler para el botón de login."""
        username = txt_usuario.value or ""
        password = txt_password.value or ""
        
        if not username or not password:
            error_text.value = "Completa todos los campos."
            page.update()
            return
        
        # Mostrar loading
        btn_login.visible = False
        loading.visible = True
        error_text.value = ""
        page.update()
        
        # Intentar login
        exito, mensaje = viewmodel.login(username, password)
        
        # Ocultar loading
        btn_login.visible = True
        loading.visible = False
        
        if exito:
            if mensaje == "CAMBIAR_PASSWORD":
                on_cambiar_password()
            else:
                on_login_success()
        else:
            error_text.value = mensaje
        
        page.update()
    
    def go_to_registro(e):
        """Handler para ir a registro."""
        on_registro()
    
    def show_recovery_dialog(e):
        """Muestra el diálogo de recuperación de contraseña."""
        txt_clave = ft.TextField(
            label="Clave de recuperación",
            hint_text="Ingresa la clave de recovery_key.txt",
            **get_input_style(is_dark),
        )
        txt_nueva = ft.TextField(
            label="Nueva contraseña",
            password=True,
            can_reveal_password=True,
            **get_input_style(is_dark),
        )
        txt_confirmar = ft.TextField(
            label="Confirmar contraseña",
            password=True,
            can_reveal_password=True,
            **get_input_style(is_dark),
        )
        error_recovery = ft.Text("", color=Colors.ERROR, size=12)
        
        # Variable para almacenar referencia al diálogo
        dlg = None
        
        def handle_cancel_recovery(e):
            """Handler para cancelar recuperación."""
            if dlg:
                page.close(dlg)
        
        def handle_recovery(e):
            """Handler para ejecutar recuperación."""
            exito, mensaje = viewmodel.recuperar_admin(
                txt_clave.value or "",
                txt_nueva.value or "",
                txt_confirmar.value or "",
            )
            
            if exito:
                if dlg:
                    page.close(dlg)
                show_snackbar(page, mensaje, "success")
            else:
                error_recovery.value = mensaje
                page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Recuperar Acceso Admin"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Ingresa la clave del archivo recovery_key.txt",
                            size=12,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Container(height=16),
                        txt_clave,
                        txt_nueva,
                        txt_confirmar,
                        error_recovery,
                    ],
                    tight=True,
                    spacing=12,
                ),
                width=350,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=handle_cancel_recovery),
                ft.ElevatedButton(
                    "Recuperar",
                    on_click=handle_recovery,
                    **get_button_style(is_primary=True),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dlg)
    
    # Asignar handlers
    btn_login.on_click = handle_login
    txt_password.on_submit = handle_login
    txt_usuario.on_submit = lambda _: txt_password.focus()
    
    # =========================================================================
    # LAYOUT
    # =========================================================================
    
    card_content = ft.Container(
        content=ft.Column(
            controls=[
                # Logo/Título
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.BOLT,
                        size=48,
                        color=Colors.PRIMARY,
                    ),
                    width=80,
                    height=80,
                    border_radius=40,
                    bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Electric Tariffs",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                ),
                ft.Text(
                    "Control de Consumo Eléctrico",
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                ),
                
                ft.Container(height=24),
                
                # Campos
                txt_usuario,
                ft.Container(height=12),
                txt_password,
                
                ft.Container(height=8),
                error_text,
                
                ft.Container(height=20),
                
                # Botón y loading
                ft.Stack(
                    controls=[
                        btn_login,
                        ft.Container(
                            content=loading,
                            alignment=ft.alignment.center,
                            width=320,
                            height=Sizes.BUTTON_HEIGHT,
                        ),
                    ],
                ),
                
                ft.Container(height=20),
                
                # Enlaces
                ft.Row(
                    controls=[
                        ft.TextButton(
                            text="Crear cuenta",
                            on_click=go_to_registro,
                            style=ft.ButtonStyle(
                                color=Colors.PRIMARY,
                            ),
                        ),
                        ft.TextButton(
                            text="¿Olvidaste tu contraseña?",
                            on_click=show_recovery_dialog,
                            style=ft.ButtonStyle(
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    width=320,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        width=Sizes.CARD_WIDTH,
        **get_card_style(is_dark),
    )
    
    return ft.Container(
        content=card_content,
        alignment=ft.alignment.center,
        expand=True,
        bgcolor=Colors.BACKGROUND_DARK if is_dark else Colors.BACKGROUND_LIGHT,
    )


# Alias para compatibilidad
LoginView = create_login_view
