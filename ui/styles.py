"""
Electric Tariffs App - Estilos y Constantes Visuales
====================================================
Según RNF-01: Color primario #219cba, fuente Inter, border_radius=15
"""

import flet as ft

from core.config import PRIMARY_COLOR, BORDER_RADIUS, FONT_FAMILY


# =============================================================================
# COLORES
# =============================================================================

class Colors:
    """Paleta de colores de la aplicación."""
    PRIMARY = PRIMARY_COLOR  # #219cba
    PRIMARY_DARK = "#1a7a94"
    PRIMARY_LIGHT = "#4bb8d4"
    
    BACKGROUND_DARK = "#1a1a2e"
    BACKGROUND_LIGHT = "#f5f5f5"
    
    SURFACE_DARK = "#252542"
    SURFACE_LIGHT = "#ffffff"
    
    TEXT_DARK = "#ffffff"
    TEXT_LIGHT = "#1a1a2e"
    TEXT_SECONDARY = "#888888"
    
    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    INFO = "#2196f3"
    
    BORDER_DARK = "#3a3a5c"
    BORDER_LIGHT = "#e0e0e0"


# =============================================================================
# DIMENSIONES
# =============================================================================

class Sizes:
    """Dimensiones estándar."""
    BORDER_RADIUS = BORDER_RADIUS  # 15
    PADDING_SM = 8
    PADDING_MD = 16
    PADDING_LG = 24
    PADDING_XL = 32
    
    BUTTON_HEIGHT = 48
    INPUT_HEIGHT = 50
    ICON_SIZE = 24
    
    SIDEBAR_WIDTH = 250
    SIDEBAR_COLLAPSED = 70
    
    CARD_WIDTH = 400
    CARD_WIDTH_SM = 320


# =============================================================================
# ESTILOS DE COMPONENTES
# =============================================================================

def get_input_style(is_dark: bool = True) -> dict:
    """Estilo para TextField."""
    return {
        "border_radius": Sizes.BORDER_RADIUS,
        "border_color": Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT,
        "focused_border_color": Colors.PRIMARY,
        "cursor_color": Colors.PRIMARY,
        "text_style": ft.TextStyle(
            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
        ),
        "label_style": ft.TextStyle(
            color=Colors.TEXT_SECONDARY,
        ),
        "height": Sizes.INPUT_HEIGHT,
        "content_padding": ft.padding.symmetric(horizontal=16, vertical=12),
    }


def get_button_style(
    is_primary: bool = True,
    is_dark: bool = True
) -> dict:
    """Estilo para ElevatedButton."""
    if is_primary:
        return {
            "bgcolor": Colors.PRIMARY,
            "color": Colors.TEXT_DARK,
            "height": Sizes.BUTTON_HEIGHT,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS),
                elevation=2,
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
    """Estilo para Card/Container."""
    return {
        "bgcolor": Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
        "border_radius": Sizes.BORDER_RADIUS,
        "padding": Sizes.PADDING_LG,
        "shadow": ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
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
