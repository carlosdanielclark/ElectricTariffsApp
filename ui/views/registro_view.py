"""
Electric Tariffs App - Vista de Registro
========================================
Pantalla de registro de nuevos usuarios con Flet.
Implementa RF-06, RF-07, RF-08.
"""

import flet as ft
from typing import Callable

from ui.styles import (
    Colors, Sizes,
    get_input_style, get_button_style, get_card_style,
    show_snackbar, create_loading_indicator,
)
from ui.viewmodels.auth_viewmodel import AuthViewModel


def create_registro_view(
    page: ft.Page,
    on_registro_success: Callable,
    on_volver_login: Callable,
    is_dark: bool = True
) -> ft.Container:
    """
    Crea la vista de registro.
    
    Args:
        page: Página Flet
        on_registro_success: Callback cuando registro exitoso
        on_volver_login: Callback para volver al login
        is_dark: Si usar tema oscuro
        
    Returns:
        Container con la vista de registro
    """
    viewmodel = AuthViewModel()
    
    # Controles
    txt_nombre = ft.TextField(
        label="Nombre completo",
        prefix_icon=ft.Icons.BADGE,
        **get_input_style(is_dark),
    )
    
    txt_usuario = ft.TextField(
        label="Usuario",
        prefix_icon=ft.Icons.PERSON,
        hint_text="Mínimo 3 caracteres",
        **get_input_style(is_dark),
    )
    
    txt_password = ft.TextField(
        label="Contraseña",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        hint_text="Mínimo 6 caracteres y 1 número",
        **get_input_style(is_dark),
    )
    
    txt_confirmar = ft.TextField(
        label="Confirmar contraseña",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
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
    
    btn_registrar = ft.ElevatedButton(
        text="Crear Cuenta",
        width=320,
        **get_button_style(is_primary=True),
    )
    
    def handle_registro(e):
        nombre = txt_nombre.value or ""
        usuario = txt_usuario.value or ""
        password = txt_password.value or ""
        confirmar = txt_confirmar.value or ""
        
        if not all([nombre, usuario, password, confirmar]):
            error_text.value = "Completa todos los campos."
            page.update()
            return
        
        # Mostrar loading
        btn_registrar.visible = False
        loading.visible = True
        error_text.value = ""
        page.update()
        
        # Intentar registro
        exito, mensaje = viewmodel.registrar(nombre, usuario, password, confirmar)
        
        # Ocultar loading
        btn_registrar.visible = True
        loading.visible = False
        
        if exito:
            show_snackbar(page, mensaje, "success")
            on_registro_success()
        else:
            error_text.value = mensaje
        
        page.update()
    
    btn_registrar.on_click = handle_registro
    txt_confirmar.on_submit = handle_registro
    txt_nombre.on_submit = lambda _: txt_usuario.focus()
    txt_usuario.on_submit = lambda _: txt_password.focus()
    txt_password.on_submit = lambda _: txt_confirmar.focus()
    
    card_content = ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=Colors.PRIMARY,
                            on_click=lambda _: on_volver_login(),
                        ),
                        ft.Text(
                            "Crear Cuenta",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                        ),
                    ],
                ),
                
                ft.Container(height=20),
                
                # Campos (RF-07)
                txt_nombre,
                ft.Container(height=8),
                txt_usuario,
                ft.Container(height=8),
                txt_password,
                ft.Container(height=8),
                txt_confirmar,
                
                ft.Container(height=8),
                
                # Requisitos de contraseña
                ft.Text(
                    "• Mínimo 6 caracteres\n• Al menos 1 número",
                    size=12,
                    color=Colors.TEXT_SECONDARY,
                ),
                
                ft.Container(height=8),
                error_text,
                
                ft.Container(height=16),
                
                # Botón
                ft.Stack(
                    controls=[
                        btn_registrar,
                        ft.Container(
                            content=loading,
                            alignment=ft.alignment.center,
                            width=320,
                            height=Sizes.BUTTON_HEIGHT,
                        ),
                    ],
                ),
                
                ft.Container(height=16),
                
                # Link volver
                ft.TextButton(
                    text="¿Ya tienes cuenta? Inicia sesión",
                    on_click=lambda _: on_volver_login(),
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
RegistroView = create_registro_view
