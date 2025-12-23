"""
Electric Tariffs App - Vista de Dashboard
=========================================
Panel de estadísticas y resumen visual.
"""

import flet as ft
from typing import Optional, Callable, List

from core.models import Medidor
from ui.viewmodels.dashboard_viewmodel import DashboardViewModel
from ui.viewmodels.medidor_viewmodel import MedidorViewModel
from ui.styles import Colors, Sizes
from ui.app_state import get_app_state


def create_dashboard_view(
    page: ft.Page,
    on_seleccionar_medidor: Callable[[Medidor], None],
    is_dark: bool = True,
) -> ft.Container:
    """
    Crea la vista del dashboard.
    
    Args:
        page: Página Flet
        on_seleccionar_medidor: Callback al seleccionar medidor
        is_dark: Si usa tema oscuro
        
    Returns:
        Container con el dashboard
    """
    vm = DashboardViewModel()
    med_vm = MedidorViewModel()
    app_state = get_app_state()
    
    # =========================================================================
    # COMPONENTES DE TARJETAS DE ESTADÍSTICAS
    # =========================================================================
    
    def crear_stat_card(
        titulo: str,
        valor: str,
        icono: str,
        color: str = Colors.PRIMARY,
        subtitulo: str = "",
    ) -> ft.Container:
        """Crea una tarjeta de estadística."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(icono, size=24, color=color),
                            ft.Text(
                                titulo,
                                size=12,
                                color=Colors.TEXT_SECONDARY,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        valor,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                    ),
                    ft.Text(
                        subtitulo,
                        size=11,
                        color=Colors.TEXT_SECONDARY,
                        visible=bool(subtitulo),
                    ),
                ],
                spacing=4,
            ),
            padding=Sizes.PADDING_MD,
            bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
            border_radius=Sizes.BORDER_RADIUS,
            expand=True,
        )
    
    # =========================================================================
    # CARGAR DATOS
    # =========================================================================
    
    resumen = vm.obtener_resumen_general()
    medidores = med_vm.obtener_medidores_usuario()
    
    # =========================================================================
    # TARJETAS DE ESTADÍSTICAS PRINCIPALES
    # =========================================================================
    
    cards_row = ft.Row(
        controls=[
            crear_stat_card(
                "Medidores",
                str(resumen["total_medidores"]),
                ft.Icons.ELECTRIC_METER,
                Colors.PRIMARY,
            ),
            crear_stat_card(
                "Total Lecturas",
                str(resumen["total_lecturas"]),
                ft.Icons.RECEIPT_LONG,
                Colors.INFO,
            ),
            crear_stat_card(
                "Consumo Mes Actual",
                f"{resumen['consumo_mes_actual']:.1f} kWh",
                ft.Icons.BOLT,
                Colors.WARNING,
            ),
            crear_stat_card(
                "Importe Mes Actual",
                f"${resumen['importe_mes_redondeado']} CUP",
                ft.Icons.ATTACH_MONEY,
                Colors.SUCCESS,
            ),
        ],
        spacing=16,
    )
    
    # =========================================================================
    # ALERTAS
    # =========================================================================
    
    alertas_contenedor = ft.Container(visible=False)
    
    if resumen["tiene_alertas"]:
        alertas_items = []
        for alerta in resumen["alertas"]:
            alertas_items.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WARNING_AMBER, color=Colors.ERROR, size=20),
                            ft.Text(
                                f"{alerta['medidor']}: Consumo {alerta['consumo']:.1f} kWh supera umbral de {alerta['umbral']:.1f} kWh",
                                size=13,
                                color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.padding.symmetric(vertical=4),
                )
            )
        
        alertas_contenedor = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=Colors.ERROR),
                            ft.Text(
                                "Alertas Activas",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.ERROR,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Column(controls=alertas_items, spacing=4),
                ],
                spacing=8,
            ),
            padding=Sizes.PADDING_MD,
            bgcolor=ft.Colors.with_opacity(0.1, Colors.ERROR),
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(1, Colors.ERROR),
            visible=True,
        )
    
    # =========================================================================
    # LISTA DE MEDIDORES CON RESUMEN
    # =========================================================================
    
    def crear_medidor_card(medidor: Medidor) -> ft.Container:
        """Crea tarjeta resumen de un medidor."""
        resumen_med = vm.obtener_resumen_medidor(medidor.id)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.ELECTRIC_METER,
                                color=Colors.PRIMARY,
                                size=24,
                            ),
                            ft.Text(
                                medidor.etiqueta,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.WARNING,
                                    color=Colors.ERROR,
                                    size=18,
                                ),
                                visible=resumen_med["alerta_activa"],
                                tooltip="Consumo sobre umbral",
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("Lecturas", size=11, color=Colors.TEXT_SECONDARY),
                                    ft.Text(str(resumen_med["total_lecturas"]), size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Mes Actual", size=11, color=Colors.TEXT_SECONDARY),
                                    ft.Text(f"{resumen_med['consumo_mes_actual']:.1f} kWh", size=14, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text("Importe", size=11, color=Colors.TEXT_SECONDARY),
                                    ft.Text(f"${resumen_med['importe_mes_redondeado']}", size=14, weight=ft.FontWeight.BOLD, color=Colors.SUCCESS),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                "Ver Lecturas",
                                icon=ft.Icons.VISIBILITY,
                                on_click=lambda e, m=medidor: on_seleccionar_medidor(m),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                spacing=8,
            ),
            padding=Sizes.PADDING_MD,
            bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(
                1,
                Colors.ERROR if resumen_med["alerta_activa"] else (Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT)
            ),
        )
    
    # Crear grid de medidores
    medidores_grid = ft.Column(
        controls=[],
        spacing=12,
    )
    
    if medidores:
        # Organizar en filas de 2
        for i in range(0, len(medidores), 2):
            fila = ft.Row(
                controls=[
                    ft.Container(
                        content=crear_medidor_card(medidores[i]),
                        expand=True,
                    ),
                ],
                spacing=16,
            )
            if i + 1 < len(medidores):
                fila.controls.append(
                    ft.Container(
                        content=crear_medidor_card(medidores[i + 1]),
                        expand=True,
                    )
                )
            medidores_grid.controls.append(fila)
    else:
        medidores_grid.controls.append(
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.ELECTRIC_METER_OUTLINED, size=48, color=Colors.TEXT_SECONDARY),
                        ft.Text(
                            "No tienes medidores registrados",
                            size=14,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "Ve a la sección 'Medidores' para agregar uno",
                            size=12,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=40,
            )
        )
    
    # =========================================================================
    # TARIFAS VIGENTES
    # =========================================================================
    
    tarifas = vm.obtener_tarifas_vigentes()
    
    tarifas_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Tramo kWh", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Precio/kWh", weight=ft.FontWeight.BOLD)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(t["tramo"])),
                    ft.DataCell(ft.Text(f"${t['precio']:.2f}")),
                ]
            )
            for t in tarifas[:5]  # Mostrar solo primeros 5 tramos
        ],
        border=ft.border.all(1, Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT),
        border_radius=Sizes.BORDER_RADIUS,
        heading_row_color=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
    )
    
    tarifas_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "Tarifas Vigentes (UNE)",
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                ),
                ft.Container(height=8),
                tarifas_table,
                ft.Text(
                    "* Se muestran los primeros 5 tramos",
                    size=11,
                    color=Colors.TEXT_SECONDARY,
                    visible=len(tarifas) > 5,
                ),
            ],
            spacing=4,
        ),
        padding=Sizes.PADDING_MD,
        bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
        border_radius=Sizes.BORDER_RADIUS,
    )
    
    # =========================================================================
    # ESTADÍSTICAS ADMIN
    # =========================================================================
    
    admin_section = ft.Container(visible=False)
    
    if app_state.es_admin:
        stats_admin = vm.obtener_estadisticas_admin()
        
        admin_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=Colors.PRIMARY),
                            ft.Text(
                                "Estadísticas del Sistema (Admin)",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            crear_stat_card(
                                "Usuarios",
                                f"{stats_admin.get('usuarios_activos', 0)}/{stats_admin.get('total_usuarios', 0)}",
                                ft.Icons.PEOPLE,
                                Colors.INFO,
                                "activos/total",
                            ),
                            crear_stat_card(
                                "Medidores Totales",
                                str(stats_admin.get('total_medidores', 0)),
                                ft.Icons.ELECTRIC_METER,
                                Colors.PRIMARY,
                            ),
                            crear_stat_card(
                                "Lecturas Totales",
                                str(stats_admin.get('total_lecturas', 0)),
                                ft.Icons.RECEIPT_LONG,
                                Colors.WARNING,
                            ),
                            crear_stat_card(
                                "Facturación Global",
                                f"${stats_admin.get('importe_global_redondeado', 0)} CUP",
                                ft.Icons.PAYMENTS,
                                Colors.SUCCESS,
                            ),
                        ],
                        spacing=16,
                    ),
                ],
                spacing=12,
            ),
            padding=Sizes.PADDING_MD,
            bgcolor=ft.Colors.with_opacity(0.05, Colors.PRIMARY),
            border_radius=Sizes.BORDER_RADIUS,
            border=ft.border.all(1, Colors.PRIMARY),
            visible=True,
        )
    
    # =========================================================================
    # LAYOUT PRINCIPAL
    # =========================================================================
    
    usuario = app_state.usuario_actual
    saludo = f"Hola, {usuario.nombre}" if usuario else "Dashboard"
    
    return ft.Container(
        content=ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.DASHBOARD, size=32, color=Colors.PRIMARY),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        saludo,
                                        size=24,
                                        weight=ft.FontWeight.BOLD,
                                        color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                                    ),
                                    ft.Text(
                                        "Resumen de tu consumo eléctrico",
                                        size=14,
                                        color=Colors.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=16,
                    ),
                    padding=Sizes.PADDING_MD,
                ),
                
                # Contenido scrolleable
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Tarjetas principales
                            cards_row,
                            
                            ft.Container(height=16),
                            
                            # Alertas
                            alertas_contenedor,
                            
                            ft.Container(height=16),
                            
                            # Sección Admin
                            admin_section,
                            
                            ft.Container(height=16) if app_state.es_admin else ft.Container(),
                            
                            # Título medidores
                            ft.Text(
                                "Mis Medidores",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                            ),
                            
                            ft.Container(height=8),
                            
                            # Grid de medidores
                            medidores_grid,
                            
                            ft.Container(height=16),
                            
                            # Tarifas
                            tarifas_card,
                            
                            ft.Container(height=32),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    padding=Sizes.PADDING_MD,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BACKGROUND_DARK if is_dark else Colors.BACKGROUND_LIGHT,
    )
