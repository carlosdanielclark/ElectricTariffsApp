"""
Electric Tariffs App - Estilos y Constantes Visuales
====================================================
Según RNF-01: Color primario #219cba, fuente Inter, border_radius=15
Diseño actualizado para coincidir con mockups HTML.
"""

import flet as ft

from core.config import PRIMARY_COLOR, BORDER_RADIUS, FONT_FAMILY


# =============================================================================
# COLORES (Actualizados según diseño HTML)
# =============================================================================

class Colors:
    """Paleta de colores de la aplicación."""
    PRIMARY = PRIMARY_COLOR  # #219cba
    PRIMARY_DARK = "#1a8da8"
    PRIMARY_LIGHT = "#4bb8d4"
    
    # Fondos según diseño HTML
    BACKGROUND_DARK = "#121d20"
    BACKGROUND_LIGHT = "#f6f7f8"
    
    # Superficies
    SURFACE_DARK = "#1a2629"
    SURFACE_LIGHT = "#ffffff"
    
    # Textos
    TEXT_DARK = "#ffffff"
    TEXT_LIGHT = "#1e293b"  # slate-800
    TEXT_SECONDARY = "#64748b"  # slate-500
    TEXT_MUTED = "#94a3b8"  # slate-400
    
    # Estados
    SUCCESS = "#22c55e"  # green-500
    WARNING = "#f97316"  # orange-500
    ERROR = "#ef4444"  # red-500
    INFO = "#3b82f6"  # blue-500
    
    # Bordes
    BORDER_DARK = "rgba(255,255,255,0.1)"
    BORDER_LIGHT = "#e5e7eb"  # gray-200
    
    # Cyan para gradientes
    CYAN_400 = "#22d3ee"


# =============================================================================
# DIMENSIONES
# =============================================================================

class Sizes:
    """Dimensiones estándar."""
    BORDER_RADIUS = 16  # Actualizado según diseño
    BORDER_RADIUS_SM = 8
    BORDER_RADIUS_LG = 24
    
    PADDING_XS = 4
    PADDING_SM = 8
    PADDING_MD = 16
    PADDING_LG = 24
    PADDING_XL = 32
    
    BUTTON_HEIGHT = 44
    INPUT_HEIGHT = 44
    ICON_SIZE = 24
    
    SIDEBAR_WIDTH = 288  # w-72 = 18rem = 288px
    HEADER_HEIGHT = 64  # h-16 = 4rem
    
    CARD_WIDTH = 400
    CARD_WIDTH_SM = 320


# =============================================================================
# ESTILOS DE COMPONENTES
# =============================================================================

def get_input_style(is_dark: bool = True) -> dict:
    """Estilo para TextField según diseño HTML."""
    return {
        "border_radius": Sizes.BORDER_RADIUS,
        "border_color": Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT,
        "focused_border_color": Colors.PRIMARY,
        "cursor_color": Colors.PRIMARY,
        "bgcolor": "rgba(0,0,0,0.2)" if is_dark else Colors.SURFACE_LIGHT,
        "text_style": ft.TextStyle(
            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
            size=14,
        ),
        "label_style": ft.TextStyle(
            color=Colors.TEXT_MUTED,
            size=12,
        ),
        "height": Sizes.INPUT_HEIGHT,
        "content_padding": ft.padding.symmetric(horizontal=12, vertical=8),
    }


def get_button_style(is_primary: bool = True, is_dark: bool = True) -> dict:
    """Estilo para ElevatedButton según diseño HTML."""
    if is_primary:
        return {
            "bgcolor": Colors.PRIMARY,
            "color": Colors.TEXT_DARK,
            "height": Sizes.BUTTON_HEIGHT,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS),
                elevation=2,
                shadow_color=ft.Colors.with_opacity(0.2, Colors.PRIMARY),
            ),
        }
    else:
        return {
            "bgcolor": "transparent",
            "color": Colors.PRIMARY,
            "height": Sizes.BUTTON_HEIGHT,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS),
                side=ft.BorderSide(1, Colors.PRIMARY),
            ),
        }


def get_card_style(is_dark: bool = True) -> dict:
    """Estilo para Card/Container según diseño HTML."""
    return {
        "bgcolor": Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
        "border_radius": Sizes.BORDER_RADIUS,
        "padding": Sizes.PADDING_LG,
        "border": ft.border.all(
            1,
            ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if is_dark else Colors.BORDER_LIGHT
        ),
        "shadow": ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    }


def get_sidebar_item_style(is_active: bool = False, is_dark: bool = True) -> dict:
    """Estilo para items del sidebar."""
    if is_active:
        return {
            "bgcolor": ft.Colors.with_opacity(0.1, Colors.PRIMARY),
            "border_radius": Sizes.BORDER_RADIUS,
            "padding": ft.padding.symmetric(horizontal=12, vertical=10),
            "border": ft.border.all(1, ft.Colors.with_opacity(0.2, Colors.PRIMARY)),
        }
    return {
        "bgcolor": "transparent",
        "border_radius": Sizes.BORDER_RADIUS,
        "padding": ft.padding.symmetric(horizontal=12, vertical=10),
    }


# =============================================================================
# TEMAS FLET
# =============================================================================

def get_dark_theme() -> ft.Theme:
    """Tema oscuro de la aplicación."""
    return ft.Theme(
        color_scheme_seed=Colors.PRIMARY,
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=Colors.TEXT_DARK,
            surface=Colors.SURFACE_DARK,
            on_surface=Colors.TEXT_DARK,
            background=Colors.BACKGROUND_DARK,
            on_background=Colors.TEXT_DARK,
            error=Colors.ERROR,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(font_family=FONT_FAMILY),
            title_large=ft.TextStyle(font_family=FONT_FAMILY, weight=ft.FontWeight.BOLD),
        ),
    )


def get_light_theme() -> ft.Theme:
    """Tema claro de la aplicación."""
    return ft.Theme(
        color_scheme_seed=Colors.PRIMARY,
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=Colors.TEXT_DARK,
            surface=Colors.SURFACE_LIGHT,
            on_surface=Colors.TEXT_LIGHT,
            background=Colors.BACKGROUND_LIGHT,
            on_background=Colors.TEXT_LIGHT,
            error=Colors.ERROR,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(font_family=FONT_FAMILY),
            title_large=ft.TextStyle(font_family=FONT_FAMILY, weight=ft.FontWeight.BOLD),
        ),
    )


# =============================================================================
# HELPERS
# =============================================================================

def show_snackbar(page: ft.Page, mensaje: str, tipo: str = "info") -> None:
    """
    Muestra un snackbar con mensaje.
    
    Args:
        page: Página Flet
        mensaje: Texto a mostrar
        tipo: 'success', 'error', 'warning', 'info'
    """
    colores = {
        "success": Colors.SUCCESS,
        "error": Colors.ERROR,
        "warning": Colors.WARNING,
        "info": Colors.INFO,
    }
    
    page.snack_bar = ft.SnackBar(
        content=ft.Text(mensaje, color=Colors.TEXT_DARK),
        bgcolor=colores.get(tipo, Colors.INFO),
        duration=3000,
    )
    page.snack_bar.open = True
    page.update()


def create_loading_indicator() -> ft.ProgressRing:
    """Crea indicador de carga."""
    return ft.ProgressRing(
        width=30,
        height=30,
        stroke_width=3,
        color=Colors.PRIMARY,
    )


def create_stat_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "bolt",
    icon_bg_color: str = None,
    is_dark: bool = True
) -> ft.Container:
    """
    Crea una tarjeta de estadística según diseño HTML.
    """
    bg_color = icon_bg_color or ft.Colors.with_opacity(0.1, Colors.PRIMARY)
    
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(
                                getattr(ft.Icons, icon.upper(), ft.Icons.BOLT),
                                color=Colors.PRIMARY,
                                size=24,
                            ),
                            width=48,
                            height=48,
                            border_radius=12,
                            bgcolor=bg_color,
                            alignment=ft.alignment.center,
                        ),
                    ],
                ),
                ft.Container(height=12),
                ft.Text(
                    title,
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                    weight=ft.FontWeight.W_500,
                ),
                ft.Text(
                    value,
                    size=28,
                    color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    subtitle,
                    size=12,
                    color=Colors.TEXT_MUTED,
                ) if subtitle else ft.Container(),
            ],
            spacing=4,
        ),
        **get_card_style(is_dark),
        expand=True,
    )
