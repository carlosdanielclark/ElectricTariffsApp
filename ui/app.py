"""
Electric Tariffs App - Aplicación Principal Flet
================================================
Orquesta navegación entre vistas y maneja el ciclo de vida.
Diseño según mockups HTML proporcionados.
"""

import flet as ft
from typing import Optional
from datetime import date

from core.models import TemaPreferido, Medidor
from ui.app_state import get_app_state
from ui.styles import (
    Colors, Sizes,
    get_dark_theme, get_light_theme,
    get_input_style, get_button_style,
    show_snackbar,
)
from ui.views.login_view import create_login_view
from ui.views.registro_view import create_registro_view
from ui.views.cambiar_password_view import create_cambiar_password_view
from ui.views.medidores_view import create_medidores_view
from ui.views.lecturas_view import create_lecturas_view
from ui.views.dashboard_view import create_dashboard_view
from ui.viewmodels.auth_viewmodel import AuthViewModel
from ui.viewmodels.lectura_viewmodel import LecturaViewModel


class ElectricTariffsApp:
    """Aplicación principal."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self._app_state = get_app_state()
        self._auth_viewmodel = AuthViewModel()
        self._lectura_viewmodel = LecturaViewModel()
        
        # Estado de navegación
        self._vista_activa = "dashboard"  # dashboard, historial, grafica, usuarios
        self._medidor_seleccionado: Optional[Medidor] = None
        
        # Estado de formularios colapsables
        self._form_lectura_expanded = False
        self._form_rapida_expanded = False
        
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
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.padding = 0
        self.page.spacing = 0
        
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
        self._vista_activa = "dashboard"
        self._medidor_seleccionado = None
        self._render_main_layout()
    
    def _navigate_to(self, vista: str) -> None:
        """Navega a una vista específica."""
        self._vista_activa = vista
        self._medidor_seleccionado = None
        self._render_main_layout()
    
    def _show_lecturas(self, medidor: Medidor) -> None:
        """Muestra las lecturas de un medidor."""
        self._vista_activa = "historial"
        self._medidor_seleccionado = medidor
        self._render_main_layout()
    
    def _render_main_layout(self) -> None:
        """Renderiza el layout principal con header, sidebar y contenido."""
        is_dark = self._is_dark()
        
        # Header
        header = self._build_header(is_dark)
        
        # Sidebar
        sidebar = self._build_sidebar(is_dark)
        
        # Contenido principal
        content = self._build_main_content(is_dark)
        
        # Layout completo
        main_layout = ft.Column(
            controls=[
                header,
                ft.Row(
                    controls=[
                        sidebar,
                        ft.Container(
                            content=content,
                            expand=True,
                            bgcolor=Colors.BACKGROUND_DARK if is_dark else Colors.BACKGROUND_LIGHT,
                            padding=Sizes.PADDING_LG,
                        ),
                    ],
                    spacing=0,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
        
        self._clear_and_show(main_layout)
    
    def _build_header(self, is_dark: bool) -> ft.Container:
        """Construye el header fijo según diseño HTML."""
        usuario = self._app_state.usuario_actual
        nombre = usuario.nombre if usuario else "Usuario"
        iniciales = "".join([n[0].upper() for n in nombre.split()[:2]])
        rol = "Administrador" if self._app_state.es_admin else "Usuario"
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    # Logo y título
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.BOLT,
                                    color=Colors.PRIMARY,
                                    size=20,
                                ),
                                width=32,
                                height=32,
                                border_radius=16,
                                bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(
                                "Electric Tariffs App",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                            ),
                        ],
                        spacing=8,
                    ),
                    # Usuario
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        nombre,
                                        size=12,
                                        weight=ft.FontWeight.W_600,
                                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                                    ),
                                    ft.Text(
                                        rol,
                                        size=10,
                                        color=Colors.TEXT_MUTED,
                                    ),
                                ],
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                            ft.Container(
                                content=ft.Container(
                                    content=ft.Text(
                                        iniciales,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=Colors.PRIMARY,
                                    ),
                                    width=32,
                                    height=32,
                                    border_radius=16,
                                    bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
                                    alignment=ft.alignment.center,
                                ),
                                width=36,
                                height=36,
                                border_radius=18,
                                gradient=ft.LinearGradient(
                                    begin=ft.alignment.top_left,
                                    end=ft.alignment.bottom_right,
                                    colors=[Colors.PRIMARY, Colors.CYAN_400],
                                ),
                                padding=2,
                            ),
                        ],
                        spacing=12,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            height=Sizes.HEADER_HEIGHT,
            bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
            padding=ft.padding.symmetric(horizontal=16),
            border=ft.border.only(
                bottom=ft.BorderSide(1, Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT)
            ),
        )
    
    def _build_sidebar(self, is_dark: bool) -> ft.Container:
        """Construye el sidebar con navegación y formularios colapsables."""
        
        # Navegación
        nav_items = [
            ("dashboard", ft.Icons.DASHBOARD, "Dashboard", self._vista_activa == "dashboard"),
            ("historial", ft.Icons.HISTORY, "Historial de lectura", self._vista_activa == "historial"),
            ("grafica", ft.Icons.SHOW_CHART, "Gráfica", self._vista_activa == "grafica"),
        ]
        
        # Solo admin puede ver gestión de usuarios
        if self._app_state.es_admin:
            nav_items.append(
                ("usuarios", ft.Icons.GROUP, "Estadísticas de usuarios", self._vista_activa == "usuarios")
            )
        
        nav_controls = []
        for vista_id, icon, texto, is_active in nav_items:
            nav_controls.append(
                self._build_nav_item(vista_id, icon, texto, is_active, is_dark)
            )
        
        # Formulario Registrar Lectura
        form_lectura = self._build_form_lectura(is_dark)
        
        # Formulario Lectura Rápida
        form_rapida = self._build_form_rapida(is_dark)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    # Navegación
                    ft.Container(
                        content=ft.Column(
                            controls=nav_controls,
                            spacing=4,
                        ),
                        padding=Sizes.PADDING_MD,
                    ),
                    
                    ft.Divider(
                        height=1,
                        color=Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT,
                    ),
                    
                    # Formularios colapsables
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                form_lectura,
                                ft.Container(height=8),
                                form_rapida,
                            ],
                            spacing=0,
                        ),
                        padding=Sizes.PADDING_MD,
                        expand=True,
                    ),
                    
                    # Botón cerrar sesión
                    ft.Container(
                        content=ft.ElevatedButton(
                            text="Cerrar sesión",
                            icon=ft.Icons.LOGOUT,
                            width=Sizes.SIDEBAR_WIDTH - 32,
                            on_click=self._handle_logout,
                            bgcolor=ft.Colors.with_opacity(0.1, Colors.ERROR),
                            color=Colors.ERROR,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=Sizes.BORDER_RADIUS),
                            ),
                        ),
                        padding=Sizes.PADDING_MD,
                        border=ft.border.only(
                            top=ft.BorderSide(1, Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT)
                        ),
                    ),
                ],
                spacing=0,
            ),
            width=Sizes.SIDEBAR_WIDTH,
            bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
            border=ft.border.only(
                right=ft.BorderSide(1, Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT)
            ),
        )
    
    def _build_nav_item(
        self,
        vista_id: str,
        icon: str,
        texto: str,
        is_active: bool,
        is_dark: bool
    ) -> ft.Container:
        """Construye un item de navegación del sidebar."""
        def on_click(e):
            self._navigate_to(vista_id)
        
        if is_active:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            icon,
                            size=20,
                            color=Colors.PRIMARY,
                        ),
                        ft.Text(
                            texto,
                            size=14,
                            weight=ft.FontWeight.W_600,
                            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                        ),
                    ],
                    spacing=12,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=Sizes.BORDER_RADIUS,
                bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, Colors.PRIMARY)),
                on_click=on_click,
            )
        else:
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            icon,
                            size=20,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            texto,
                            size=14,
                            weight=ft.FontWeight.W_500,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=12,
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                border_radius=Sizes.BORDER_RADIUS,
                on_click=on_click,
                ink=True,
            )
    
    def _build_form_lectura(self, is_dark: bool) -> ft.Container:
        """Construye el formulario colapsable de Registrar Lectura."""
        # Campos del formulario
        txt_fecha_inicio = ft.TextField(
            label="Fecha inicio",
            value=str(date.today()),
            **get_input_style(is_dark),
        )
        txt_fecha_fin = ft.TextField(
            label="Fecha fin",
            value=str(date.today()),
            **get_input_style(is_dark),
        )
        txt_referencia = ft.TextField(
            label="Lectura de referencia",
            hint_text="0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        txt_actual = ft.TextField(
            label="Lectura actual",
            hint_text="0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        
        # Contenido del formulario
        form_content = ft.Container(
            content=ft.Column(
                controls=[
                    txt_fecha_inicio,
                    txt_fecha_fin,
                    txt_referencia,
                    txt_actual,
                    ft.ElevatedButton(
                        text="Guardar Lectura",
                        width=Sizes.SIDEBAR_WIDTH - 64,
                        **get_button_style(is_primary=True),
                        on_click=lambda e: self._save_lectura(
                            txt_fecha_inicio.value,
                            txt_fecha_fin.value,
                            txt_referencia.value,
                            txt_actual.value,
                        ),
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.only(left=16, right=16, bottom=16),
            visible=self._form_lectura_expanded,
        )
        
        def toggle_form(e):
            self._form_lectura_expanded = not self._form_lectura_expanded
            form_content.visible = self._form_lectura_expanded
            icon.name = ft.Icons.EXPAND_LESS if self._form_lectura_expanded else ft.Icons.EXPAND_MORE
            self.page.update()
        
        icon = ft.Icon(
            ft.Icons.EXPAND_MORE,
            color=Colors.PRIMARY,
            size=20,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.EDIT_NOTE, color=Colors.PRIMARY, size=18),
                                        ft.Text(
                                            "REGISTRAR LECTURA",
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=Colors.PRIMARY,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                icon,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=Sizes.PADDING_MD,
                        on_click=toggle_form,
                        ink=True,
                        border_radius=ft.border_radius.only(
                            top_left=Sizes.BORDER_RADIUS,
                            top_right=Sizes.BORDER_RADIUS,
                        ),
                    ),
                    form_content,
                ],
                spacing=0,
            ),
            bgcolor=ft.Colors.with_opacity(0.05, Colors.PRIMARY) if is_dark else "#f9fafb",
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(
                1,
                ft.Colors.with_opacity(0.1, Colors.PRIMARY) if is_dark else "#e5e7eb"
            ),
        )
    
    def _build_form_rapida(self, is_dark: bool) -> ft.Container:
        """Construye el formulario colapsable de Lectura Rápida."""
        txt_inicial = ft.TextField(
            label="Lectura inicial",
            hint_text="0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        txt_final = ft.TextField(
            label="Lectura final",
            hint_text="0000",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        
        resultado_text = ft.Text(
            "",
            size=14,
            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
            text_align=ft.TextAlign.CENTER,
        )
        
        def calcular_rapida(e):
            try:
                inicial = float(txt_inicial.value or 0)
                final = float(txt_final.value or 0)
                consumo = final - inicial
                if consumo < 0:
                    consumo = (99999.9 - inicial) + final
                
                # Calcular importe usando las tarifas
                from core.actions import calcular_importe_por_tramos
                importe = calcular_importe_por_tramos(consumo)
                
                resultado_text.value = f"Consumo: {consumo:.1f} kWh\nImporte: ${importe:,.0f} CUP"
                self.page.update()
            except Exception as ex:
                show_snackbar(self.page, f"Error: {str(ex)}", "error")
        
        form_content = ft.Container(
            content=ft.Column(
                controls=[
                    txt_inicial,
                    txt_final,
                    ft.ElevatedButton(
                        text="Calcular",
                        width=Sizes.SIDEBAR_WIDTH - 64,
                        icon=ft.Icons.FLASH_ON,
                        **get_button_style(is_primary=True),
                        on_click=calcular_rapida,
                    ),
                    resultado_text,
                ],
                spacing=12,
            ),
            padding=ft.padding.only(left=16, right=16, bottom=16),
            visible=self._form_rapida_expanded,
        )
        
        def toggle_form(e):
            self._form_rapida_expanded = not self._form_rapida_expanded
            form_content.visible = self._form_rapida_expanded
            icon.name = ft.Icons.EXPAND_LESS if self._form_rapida_expanded else ft.Icons.EXPAND_MORE
            self.page.update()
        
        icon = ft.Icon(
            ft.Icons.EXPAND_MORE,
            color=Colors.PRIMARY,
            size=20,
        )
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.FLASH_ON, color=Colors.PRIMARY, size=18),
                                        ft.Text(
                                            "LECTURA RÁPIDA",
                                            size=12,
                                            weight=ft.FontWeight.BOLD,
                                            color=Colors.PRIMARY,
                                        ),
                                    ],
                                    spacing=8,
                                ),
                                icon,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        padding=Sizes.PADDING_MD,
                        on_click=toggle_form,
                        ink=True,
                        border_radius=ft.border_radius.only(
                            top_left=Sizes.BORDER_RADIUS,
                            top_right=Sizes.BORDER_RADIUS,
                        ),
                    ),
                    form_content,
                ],
                spacing=0,
            ),
            bgcolor=ft.Colors.with_opacity(0.05, Colors.PRIMARY) if is_dark else "#f9fafb",
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(
                1,
                ft.Colors.with_opacity(0.1, Colors.PRIMARY) if is_dark else "#e5e7eb"
            ),
        )
    
    def _build_main_content(self, is_dark: bool) -> ft.Control:
        """Construye el contenido principal según la vista activa."""
        if self._vista_activa == "dashboard":
            return create_dashboard_view(
                page=self.page,
                on_seleccionar_medidor=self._on_seleccionar_medidor,
                is_dark=is_dark,
            )
        elif self._vista_activa == "historial":
            if self._medidor_seleccionado:
                return create_lecturas_view(
                    page=self.page,
                    medidor=self._medidor_seleccionado,
                    on_volver=lambda: self._navigate_to("dashboard"),
                    is_dark=is_dark,
                )
            else:
                # Vista de medidores para seleccionar
                return create_medidores_view(
                    page=self.page,
                    on_seleccionar_medidor=self._on_seleccionar_medidor,
                    is_dark=is_dark,
                )
        elif self._vista_activa == "grafica":
            return self._build_grafica_view(is_dark)
        elif self._vista_activa == "usuarios":
            return self._build_usuarios_view(is_dark)
        else:
            return ft.Text("Vista no encontrada")
    
    def _build_grafica_view(self, is_dark: bool) -> ft.Container:
        """Construye la vista de gráfica (placeholder)."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Gráfica de Consumo",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                    ),
                    ft.Text(
                        "Visualización del consumo eléctrico a lo largo del tiempo.",
                        size=14,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Icon(
                                    ft.Icons.SHOW_CHART,
                                    size=64,
                                    color=Colors.TEXT_MUTED,
                                ),
                                ft.Text(
                                    "Próximamente",
                                    size=16,
                                    color=Colors.TEXT_MUTED,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=16,
                        ),
                        alignment=ft.alignment.center,
                        expand=True,
                    ),
                ],
            ),
            expand=True,
        )
    
    def _build_usuarios_view(self, is_dark: bool) -> ft.Container:
        """Construye la vista de gestión de usuarios (solo admin)."""
        if not self._app_state.es_admin:
            return ft.Container(
                content=ft.Text(
                    "Acceso denegado",
                    color=Colors.ERROR,
                ),
            )
        
        from ui.viewmodels.dashboard_viewmodel import DashboardViewModel
        dashboard_vm = DashboardViewModel()
        stats = dashboard_vm.obtener_estadisticas_admin()
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Estadísticas de Usuarios",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                    ),
                    ft.Text(
                        "Panel de administración de usuarios del sistema.",
                        size=14,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Container(height=24),
                    ft.Row(
                        controls=[
                            self._build_stat_card(
                                "Total Usuarios",
                                str(stats.get("total_usuarios", 0)),
                                ft.Icons.PEOPLE,
                                is_dark,
                            ),
                            self._build_stat_card(
                                "Usuarios Activos",
                                str(stats.get("usuarios_activos", 0)),
                                ft.Icons.PERSON_PIN,
                                is_dark,
                            ),
                            self._build_stat_card(
                                "Total Medidores",
                                str(stats.get("total_medidores", 0)),
                                ft.Icons.ELECTRIC_METER,
                                is_dark,
                            ),
                        ],
                        spacing=16,
                    ),
                ],
            ),
            expand=True,
        )
    
    def _build_stat_card(
        self,
        title: str,
        value: str,
        icon: str,
        is_dark: bool
    ) -> ft.Container:
        """Construye una tarjeta de estadística."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, color=Colors.PRIMARY, size=24),
                        width=48,
                        height=48,
                        border_radius=12,
                        bgcolor=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        title,
                        size=12,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    ft.Text(
                        value,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                    ),
                ],
                spacing=8,
            ),
            padding=Sizes.PADDING_LG,
            bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(
                1,
                ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if is_dark else Colors.BORDER_LIGHT
            ),
            expand=True,
        )
    
    def _save_lectura(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        referencia: str,
        actual: str
    ) -> None:
        """Guarda una nueva lectura desde el formulario del sidebar."""
        try:
            if not all([fecha_inicio, fecha_fin, referencia, actual]):
                show_snackbar(self.page, "Completa todos los campos", "warning")
                return
            
            # Validar que haya un medidor seleccionado o usar el primero
            from data.repositories import MedidorRepository
            medidor_repo = MedidorRepository()
            medidores = medidor_repo.obtener_por_usuario(self._app_state.usuario_id)
            
            if not medidores:
                show_snackbar(self.page, "No tienes medidores. Crea uno primero.", "warning")
                return
            
            medidor = medidores[0]
            
            # Crear lectura
            exito, mensaje, _ = self._lectura_viewmodel.crear_lectura(
                medidor_id=medidor.id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                lectura_actual=float(actual),
            )
            
            if exito:
                show_snackbar(self.page, mensaje, "success")
                self._navigate_to("dashboard")
            else:
                show_snackbar(self.page, mensaje, "error")
                
        except Exception as ex:
            show_snackbar(self.page, f"Error: {str(ex)}", "error")
    
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


def run_app() -> None:
    """Punto de entrada para ejecutar la aplicación Flet."""
    ft.app(target=lambda page: ElectricTariffsApp(page))
