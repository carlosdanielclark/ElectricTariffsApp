"""
Electric Tariffs App - Aplicación Principal Flet
================================================
Orquesta navegación entre vistas y maneja el ciclo de vida.
"""

import flet as ft
from typing import Optional

from core.models import TemaPreferido, Medidor
from ui.app_state import get_app_state
from ui.styles import (
    Colors, Sizes,
    get_dark_theme, get_light_theme,
    show_snackbar,
)
from ui.views.login_view import create_login_view
from ui.views.registro_view import create_registro_view
from ui.views.cambiar_password_view import create_cambiar_password_view
from ui.views.medidores_view import create_medidores_view
from ui.views.lecturas_view import create_lecturas_view
from ui.views.dashboard_view import create_dashboard_view
from ui.viewmodels.auth_viewmodel import AuthViewModel


class ElectricTariffsApp:
    """Aplicación principal."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._app_state = get_app_state()
        self._auth_viewmodel = AuthViewModel()
        self._vista_activa = "medidores"  # medidores, dashboard, lecturas
        self._medidor_seleccionado: Optional[Medidor] = None
        
        # Configuración de la página
        self._setup_page()
        
        # Configurar callbacks del estado
        self._app_state.set_logout_callback(self._on_logout)
        self._app_state.set_theme_change_callback(self._on_theme_change)
        
        # Mostrar vista inicial
        self._show_login()
    
    def _setup_page(self) -> None:
        """Configura la página principal."""
        self.page.title = "Electric Tariffs App"
        self.page.window.width = 1200
        self.page.window.height = 800
        self.page.window.min_width = 400
        self.page.window.min_height = 600
        
        # Tema inicial
        self._apply_theme(self._app_state.tema_actual)
        
        self.page.update()
    
    def _apply_theme(self, tema: TemaPreferido) -> None:
        """Aplica el tema visual."""
        if tema == TemaPreferido.OSCURO:
            self.page.theme = get_dark_theme()
            self.page.dark_theme = get_dark_theme()
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = Colors.BACKGROUND_DARK
        else:
            self.page.theme = get_light_theme()
            self.page.dark_theme = get_light_theme()
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = Colors.BACKGROUND_LIGHT
        
        self.page.update()
    
    def _is_dark(self) -> bool:
        """Verifica si el tema actual es oscuro."""
        return self._app_state.tema_actual == TemaPreferido.OSCURO
    
    # =========================================================================
    # NAVEGACIÓN
    # =========================================================================
    
    def _clear_and_show(self, control: ft.Control) -> None:
        """Limpia la página y muestra un control."""
        self.page.controls.clear()
        self.page.controls.append(control)
        self.page.update()
    
    def _show_login(self) -> None:
        """Muestra la pantalla de login."""
        view = create_login_view(
            page=self.page,
            on_login_success=self._on_login_success,
            on_registro=self._show_registro,
            on_cambiar_password=self._show_cambiar_password_obligatorio,
            is_dark=self._is_dark(),
        )
        self._clear_and_show(view)
    
    def _show_registro(self) -> None:
        """Muestra la pantalla de registro."""
        view = create_registro_view(
            page=self.page,
            on_registro_success=self._show_login,
            on_volver_login=self._show_login,
            is_dark=self._is_dark(),
        )
        self._clear_and_show(view)
    
    def _show_cambiar_password_obligatorio(self) -> None:
        """Muestra la pantalla de cambio obligatorio de contraseña."""
        view = create_cambiar_password_view(
            page=self.page,
            on_success=self._on_login_success,
            es_obligatorio=True,
            is_dark=self._is_dark(),
        )
        self._clear_and_show(view)
    
    def _show_main_app(self) -> None:
        """Muestra la aplicación principal después del login."""
        self._vista_activa = "medidores"
        self._medidor_seleccionado = None
        self._render_main_layout()
    
    def _show_dashboard(self) -> None:
        """Muestra el dashboard."""
        self._vista_activa = "dashboard"
        self._medidor_seleccionado = None
        self._render_main_layout()
    
    def _show_lecturas(self, medidor: Medidor) -> None:
        """Muestra las lecturas de un medidor."""
        self._vista_activa = "lecturas"
        self._medidor_seleccionado = medidor
        self._render_main_layout()
    
    def _render_main_layout(self) -> None:
        """Renderiza el layout principal con la vista activa."""
        # Determinar contenido según vista activa
        if self._vista_activa == "dashboard":
            content = create_dashboard_view(
                page=self.page,
                on_seleccionar_medidor=self._on_seleccionar_medidor,
                is_dark=self._is_dark(),
            )
        elif self._vista_activa == "lecturas" and self._medidor_seleccionado:
            content = create_lecturas_view(
                page=self.page,
                medidor=self._medidor_seleccionado,
                on_volver=self._show_main_app,
                is_dark=self._is_dark(),
            )
        else:
            # Vista por defecto: medidores
            content = create_medidores_view(
                page=self.page,
                on_seleccionar_medidor=self._on_seleccionar_medidor,
                is_dark=self._is_dark(),
            )
        
        # Sidebar
        sidebar = self._build_sidebar()
        
        # Layout principal
        main_layout = ft.Row(
            controls=[
                sidebar,
                ft.VerticalDivider(width=1, color=Colors.BORDER_DARK if self._is_dark() else Colors.BORDER_LIGHT),
                ft.Container(
                    content=content,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        self._clear_and_show(main_layout)
    
    def _build_sidebar(self) -> ft.Container:
        """Construye el sidebar de navegación."""
        usuario = self._app_state.usuario_actual
        nombre = usuario.nombre if usuario else "Usuario"
        rol = "Administrador" if self._app_state.es_admin else "Usuario"
        
        # Items del menú con estado activo
        menu_items = [
            self._build_menu_item(
                ft.Icons.DASHBOARD,
                "Dashboard",
                self._show_dashboard,
                self._vista_activa == "dashboard"
            ),
            self._build_menu_item(
                ft.Icons.ELECTRIC_METER,
                "Medidores",
                self._show_main_app,
                self._vista_activa == "medidores"
            ),
        ]
        
        # Items admin
        if self._app_state.es_admin:
            menu_items.extend([
                ft.Divider(height=1, color=Colors.BORDER_DARK if self._is_dark() else Colors.BORDER_LIGHT),
                self._build_menu_item(ft.Icons.PEOPLE, "Usuarios", None, False),
                self._build_menu_item(ft.Icons.PRICE_CHANGE, "Tarifas", None, False),
            ])
        
        # Toggle de tema
        tema_switch = ft.Switch(
            value=self._is_dark(),
            label="Modo Oscuro",
            on_change=self._toggle_theme,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Header del sidebar
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.BOLT,
                                    size=40,
                                    color=Colors.PRIMARY,
                                ),
                                ft.Text(
                                    "Electric Tariffs",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=Colors.TEXT_DARK if self._is_dark() else Colors.TEXT_LIGHT,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        padding=Sizes.PADDING_LG,
                    ),
                    
                    ft.Divider(height=1, color=Colors.BORDER_DARK if self._is_dark() else Colors.BORDER_LIGHT),
                    
                    # Usuario actual
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.CircleAvatar(
                                    content=ft.Text(nombre[0].upper()),
                                    bgcolor=Colors.PRIMARY,
                                    radius=20,
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text(
                                            nombre,
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=Colors.TEXT_DARK if self._is_dark() else Colors.TEXT_LIGHT,
                                        ),
                                        ft.Text(
                                            rol,
                                            size=12,
                                            color=Colors.TEXT_SECONDARY,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            spacing=12,
                        ),
                        padding=Sizes.PADDING_MD,
                    ),
                    
                    ft.Divider(height=1, color=Colors.BORDER_DARK if self._is_dark() else Colors.BORDER_LIGHT),
                    
                    # Menú
                    ft.Container(
                        content=ft.Column(
                            controls=menu_items,
                            spacing=4,
                        ),
                        padding=Sizes.PADDING_SM,
                        expand=True,
                    ),
                    
                    # Footer
                    ft.Divider(height=1, color=Colors.BORDER_DARK if self._is_dark() else Colors.BORDER_LIGHT),
                    
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                tema_switch,
                                ft.ElevatedButton(
                                    text="Cerrar Sesión",
                                    icon=ft.Icons.LOGOUT,
                                    width=Sizes.SIDEBAR_WIDTH - 32,
                                    on_click=self._handle_logout,
                                    bgcolor=Colors.ERROR,
                                    color=Colors.TEXT_DARK,
                                ),
                            ],
                            spacing=12,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=Sizes.PADDING_MD,
                    ),
                ],
                spacing=0,
            ),
            width=Sizes.SIDEBAR_WIDTH,
            bgcolor=Colors.SURFACE_DARK if self._is_dark() else Colors.SURFACE_LIGHT,
        )
    
    def _build_menu_item(
        self,
        icon: str,
        text: str,
        on_click,
        is_active: bool
    ) -> ft.Container:
        """Construye un item del menú sidebar."""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        icon,
                        size=Sizes.ICON_SIZE,
                        color=Colors.PRIMARY if is_active else Colors.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        text,
                        size=14,
                        color=Colors.TEXT_DARK if self._is_dark() else Colors.TEXT_LIGHT,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            border_radius=Sizes.BORDER_RADIUS,
            bgcolor=ft.colors.with_opacity(0.1, Colors.PRIMARY) if is_active else None,
            on_click=lambda _: on_click() if on_click else None,
            ink=True,
        )
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def _on_login_success(self) -> None:
        """Callback cuando el login es exitoso."""
        self._apply_theme(self._app_state.tema_actual)
        self._show_main_app()
    
    def _on_logout(self) -> None:
        """Callback cuando se cierra sesión."""
        self._show_login()
    
    def _on_theme_change(self, tema: TemaPreferido) -> None:
        """Callback cuando cambia el tema."""
        self._apply_theme(tema)
    
    def _on_seleccionar_medidor(self, medidor: Medidor) -> None:
        """Callback cuando se selecciona un medidor."""
        self._show_lecturas(medidor)
    
    def _handle_logout(self, e) -> None:
        """Maneja el cierre de sesión."""
        self._auth_viewmodel.logout()
    
    def _toggle_theme(self, e) -> None:
        """Alterna entre tema oscuro y claro."""
        nuevo_tema = TemaPreferido.OSCURO if e.control.value else TemaPreferido.CLARO
        self._app_state.tema_actual = nuevo_tema
        
        # Guardar preferencia en BD si hay usuario
        if self._app_state.usuario_actual:
            from data.repositories import UsuarioRepository
            repo = UsuarioRepository()
            repo.update_tema(self._app_state.usuario_id, nuevo_tema)
        
        # Recargar la vista principal para aplicar el tema
        self._show_main_app()


def run_app() -> None:
    """Punto de entrada para ejecutar la aplicación Flet."""
    ft.app(target=lambda page: ElectricTariffsApp(page))
