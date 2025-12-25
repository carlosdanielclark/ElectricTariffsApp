"""
Electric Tariffs App - Vista de Cambio de Contraseña
===================================================
Pantalla para cambio obligatorio de contraseña (RF-02).
"""

import flet as ft
from typing import Callable, Optional

from ui.styles import (
    Colors, Sizes,
    get_input_style, get_button_style, get_card_style,
    show_snackbar, create_loading_indicator,
)
from ui.viewmodels.auth_viewmodel import AuthViewModel


def create_cambiar_password_view(
    page: ft.Page,
    on_success: Callable,
    on_cancel: Optional[Callable] = None,
    es_obligatorio: bool = False,
    is_dark: bool = True
) -> ft.Container:
    """
    Crea la vista de cambio de contraseña.
    
    Args:
        page: Página Flet
        on_success: Callback cuando cambio exitoso
        on_cancel: Callback para cancelar (solo si no es obligatorio)
        es_obligatorio: Si es cambio obligatorio (RF-02)
        is_dark: Si usar tema oscuro
        
    Returns:
        Container con la vista
    """
    viewmodel = AuthViewModel()
    
    # Controles
    txt_actual = ft.TextField(
        label="Contraseña actual",
        prefix_icon=ft.Icons.LOCK_OPEN,
        password=True,
        can_reveal_password=True,
        **get_input_style(is_dark),
    )
    
    txt_nueva = ft.TextField(
        label="Nueva contraseña",
        prefix_icon=ft.Icons.LOCK,
        password=True,
        can_reveal_password=True,
        hint_text="Mínimo 6 caracteres y 1 número",
        **get_input_style(is_dark),
    )
    
    txt_confirmar = ft.TextField(
        label="Confirmar nueva contraseña",
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
    
    btn_cambiar = ft.ElevatedButton(
        text="Cambiar Contraseña",
        width=320,
        **get_button_style(is_primary=True),
    )
    
    # =========================================================================
    # HANDLERS - Definidos como funciones para evitar problemas con lambdas
    # =========================================================================
    
    def handle_cambiar(e):
        """Handler para el botón de cambiar contraseña."""
        actual = txt_actual.value or ""
        nueva = txt_nueva.value or ""
        confirmar = txt_confirmar.value or ""
        
        if not all([actual, nueva, confirmar]):
            error_text.value = "Completa todos los campos."
            page.update()
            return
        
        # Mostrar loading
        btn_cambiar.visible = False
        loading.visible = True
        error_text.value = ""
        page.update()
        
        # Intentar cambio
        exito, mensaje = viewmodel.cambiar_password(actual, nueva, confirmar)
        
        # Ocultar loading
        btn_cambiar.visible = True
        loading.visible = False
        
        if exito:
            show_snackbar(page, mensaje, "success")
            on_success()
        else:
            error_text.value = mensaje
        
        page.update()
    
    def handle_cancel(e):
        """Handler para el botón de cancelar."""
        if on_cancel:
            on_cancel()
    
    # Asignar handlers
    btn_cambiar.on_click = handle_cambiar
    txt_confirmar.on_submit = handle_cambiar
    txt_actual.on_submit = lambda _: txt_nueva.focus()
    txt_nueva.on_submit = lambda _: txt_confirmar.focus()
    
    # =========================================================================
    # LAYOUT
    # =========================================================================
    
    # Header con icono de advertencia si es obligatorio
    header_controls = [
        ft.Icon(
            ft.Icons.WARNING_AMBER if es_obligatorio else ft.Icons.LOCK_RESET,
            size=48,
            color=Colors.WARNING if es_obligatorio else Colors.PRIMARY,
        ),
        ft.Text(
            "Cambio Obligatorio" if es_obligatorio else "Cambiar Contraseña",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
        ),
    ]
    
    if es_obligatorio:
        header_controls.append(
            ft.Text(
                "Por seguridad, debes cambiar tu contraseña inicial.",
                size=14,
                color=Colors.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
            )
        )
    
    # Botones de acción
    action_controls = [
        ft.Stack(
            controls=[
                btn_cambiar,
                ft.Container(
                    content=loading,
                    alignment=ft.alignment.center,
                    width=320,
                    height=Sizes.BUTTON_HEIGHT,
                ),
            ],
        ),
    ]
    
    # Botón cancelar solo si no es obligatorio
    if not es_obligatorio and on_cancel:
        action_controls.append(
            ft.TextButton(
                text="Cancelar",
                on_click=handle_cancel,
            )
        )
    
    card_content = ft.Container(
        content=ft.Column(
            controls=[
                *header_controls,
                
                ft.Container(height=20),
                
                # Campos
                txt_actual,
                ft.Container(height=8),
                txt_nueva,
                ft.Container(height=8),
                txt_confirmar,
                
                ft.Container(height=8),
                error_text,
                
                ft.Container(height=16),
                
                # Botones
                *action_controls,
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
CambiarPasswordView = create_cambiar_password_view
