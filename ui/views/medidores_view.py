"""
Electric Tariffs App - Vista de Medidores
=========================================
Pantalla de gestión CRUD de medidores con Flet.
Implementa RF-13 a RF-17.
"""

import flet as ft
from typing import Callable, Optional

from core.models import Medidor
from ui.styles import (
    Colors, Sizes,
    get_input_style, get_button_style, get_card_style,
    show_snackbar, create_loading_indicator,
)
from ui.viewmodels.medidor_viewmodel import MedidorViewModel
from ui.app_state import get_app_state


def create_medidores_view(
    page: ft.Page,
    on_seleccionar_medidor: Optional[Callable[[Medidor], None]] = None,
    is_dark: bool = True
) -> ft.Container:
    """
    Crea la vista de gestión de medidores.
    
    Args:
        page: Página Flet
        on_seleccionar_medidor: Callback cuando se selecciona un medidor
        is_dark: Si usar tema oscuro
        
    Returns:
        Container con la vista de medidores
    """
    viewmodel = MedidorViewModel()
    app_state = get_app_state()
    
    # Controles
    lista_medidores = ft.ListView(
        expand=True,
        spacing=12,
        padding=Sizes.PADDING_MD,
    )
    
    loading = create_loading_indicator()
    loading.visible = False
    
    empty_state = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.ELECTRIC_METER_OUTLINED,
                    size=64,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    "No tienes medidores registrados",
                    size=16,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    "Crea uno para comenzar a registrar lecturas",
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.alignment.center,
        expand=True,
        visible=False,
    )
    
    def crear_card_medidor(medidor: Medidor) -> ft.Container:
        """Crea una tarjeta para mostrar un medidor."""
        es_propietario = viewmodel.es_propietario(medidor.id)
        stats = viewmodel.obtener_estadisticas_medidor(medidor.id)
        
        # Indicador de tipo de acceso
        tipo_badge = ft.Container(
            content=ft.Text(
                "PROPIETARIO" if es_propietario else "VINCULADO",
                size=10,
                weight=ft.FontWeight.BOLD,
                color=Colors.TEXT_DARK,
            ),
            bgcolor=Colors.PRIMARY if es_propietario else Colors.INFO,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
        )
        
        # Calcular texto de umbral
        umbral_texto = f"{stats['umbral']:.0f} kWh" if stats['tiene_umbral'] else "No configurada"
        
        # Info del medidor
        info_column = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            medidor.etiqueta,
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                        ),
                        tipo_badge,
                    ],
                    spacing=8,
                ),
                ft.Text(
                    f"Serie: {medidor.numero_serie or 'No especificado'}",
                    size=13,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    f"Lecturas: {stats['cantidad_lecturas']} | Alerta: {umbral_texto}",
                    size=12,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            spacing=4,
            expand=True,
        )
        
        # Botones de acción
        acciones = []
        
        if on_seleccionar_medidor:
            acciones.append(
                ft.IconButton(
                    icon=ft.Icons.VISIBILITY,
                    icon_color=Colors.PRIMARY,
                    tooltip="Ver lecturas",
                    on_click=lambda _, m=medidor: on_seleccionar_medidor(m),
                )
            )
        
        if es_propietario or app_state.es_admin:
            acciones.extend([
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=Colors.INFO,
                    tooltip="Editar",
                    on_click=lambda _, m=medidor: show_editar_dialog(m),
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=Colors.ERROR,
                    tooltip="Eliminar",
                    on_click=lambda _, m=medidor: show_eliminar_dialog(m),
                ),
            ])
        
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.ELECTRIC_METER,
                        size=40,
                        color=Colors.PRIMARY,
                    ),
                    info_column,
                    ft.Row(controls=acciones),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **get_card_style(is_dark),
            on_click=lambda _, m=medidor: (
                on_seleccionar_medidor(m) if on_seleccionar_medidor else None
            ),
        )
    
    def cargar_medidores():
        """Carga la lista de medidores."""
        loading.visible = True
        lista_medidores.controls.clear()
        empty_state.visible = False
        page.update()
        
        medidores = viewmodel.obtener_medidores_usuario()
        
        loading.visible = False
        
        if not medidores:
            empty_state.visible = True
        else:
            for medidor in medidores:
                lista_medidores.controls.append(crear_card_medidor(medidor))
        
        page.update()
    
    def show_crear_dialog(e):
        """Muestra diálogo para crear nuevo medidor."""
        txt_etiqueta = ft.TextField(
            label="Etiqueta *",
            hint_text="Ej: Casa, Taller, Local",
            **get_input_style(is_dark),
        )
        txt_serie = ft.TextField(
            label="Número de serie (opcional)",
            **get_input_style(is_dark),
        )
        txt_umbral = ft.TextField(
            label="Umbral de alerta kWh (opcional)",
            hint_text="Ej: 300",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        error_text = ft.Text("", color=Colors.ERROR, size=12)
        
        def handle_crear(e):
            umbral = None
            if txt_umbral.value:
                try:
                    umbral = float(txt_umbral.value)
                except ValueError:
                    error_text.value = "El umbral debe ser un número."
                    page.update()
                    return
            
            exito, mensaje, medidor = viewmodel.crear_medidor(
                txt_etiqueta.value or "",
                txt_serie.value,
                umbral,
            )
            
            if exito:
                page.close(dlg)
                show_snackbar(page, mensaje, "success")
                cargar_medidores()
            else:
                error_text.value = mensaje
                page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nuevo Medidor"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        txt_etiqueta,
                        txt_serie,
                        txt_umbral,
                        error_text,
                    ],
                    tight=True,
                    spacing=12,
                ),
                width=350,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)),
                ft.ElevatedButton(
                    "Crear",
                    on_click=handle_crear,
                    **get_button_style(is_primary=True),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dlg)
    
    def show_editar_dialog(medidor: Medidor):
        """Muestra diálogo para editar medidor."""
        txt_etiqueta = ft.TextField(
            label="Etiqueta *",
            value=medidor.etiqueta,
            **get_input_style(is_dark),
        )
        txt_serie = ft.TextField(
            label="Número de serie (opcional)",
            value=medidor.numero_serie or "",
            **get_input_style(is_dark),
        )
        txt_umbral = ft.TextField(
            label="Umbral de alerta kWh (opcional)",
            value=str(medidor.umbral_alerta) if medidor.umbral_alerta else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            **get_input_style(is_dark),
        )
        error_text = ft.Text("", color=Colors.ERROR, size=12)
        
        def handle_editar(e):
            umbral = None
            if txt_umbral.value:
                try:
                    umbral = float(txt_umbral.value)
                except ValueError:
                    error_text.value = "El umbral debe ser un número."
                    page.update()
                    return
            
            exito, mensaje = viewmodel.actualizar_medidor(
                medidor.id,
                txt_etiqueta.value or "",
                txt_serie.value,
                umbral,
            )
            
            if exito:
                page.close(dlg)
                show_snackbar(page, mensaje, "success")
                cargar_medidores()
            else:
                error_text.value = mensaje
                page.update()
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Editar: {medidor.etiqueta}"),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        txt_etiqueta,
                        txt_serie,
                        txt_umbral,
                        error_text,
                    ],
                    tight=True,
                    spacing=12,
                ),
                width=350,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)),
                ft.ElevatedButton(
                    "Guardar",
                    on_click=handle_editar,
                    **get_button_style(is_primary=True),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dlg)
    
    def show_eliminar_dialog(medidor: Medidor):
        """Muestra diálogo de confirmación para eliminar medidor."""
        stats = viewmodel.obtener_estadisticas_medidor(medidor.id)
        
        mensaje = f"¿Eliminar el medidor '{medidor.etiqueta}'?"
        if stats["cantidad_lecturas"] > 0:
            mensaje += f"\n\n⚠️ Se eliminarán {stats['cantidad_lecturas']} lectura(s)."
        
        def handle_eliminar(e):
            exito, mensaje_result, _ = viewmodel.eliminar_medidor(
                medidor.id,
                confirmar=True,
            )
            
            page.close(dlg)
            
            if exito:
                show_snackbar(page, mensaje_result, "success")
                cargar_medidores()
            else:
                show_snackbar(page, mensaje_result, "error")
        
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación"),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: page.close(dlg)),
                ft.ElevatedButton(
                    "Eliminar",
                    bgcolor=Colors.ERROR,
                    color=Colors.TEXT_DARK,
                    on_click=handle_eliminar,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        page.open(dlg)
    
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    "Mis Medidores",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                ),
                ft.ElevatedButton(
                    text="Nuevo Medidor",
                    icon=ft.Icons.ADD,
                    on_click=show_crear_dialog,
                    **get_button_style(is_primary=True),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=Sizes.PADDING_MD,
    )
    
    # Cargar medidores al crear la vista
    page.on_view_pop = lambda _: cargar_medidores()
    
    # Container principal con función de refresh expuesta
    container = ft.Container(
        content=ft.Column(
            controls=[
                header,
                ft.Container(
                    content=ft.Stack(
                        controls=[
                            lista_medidores,
                            empty_state,
                            ft.Container(
                                content=loading,
                                alignment=ft.alignment.center,
                                expand=True,
                            ),
                        ],
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        ),
        expand=True,
        bgcolor=Colors.BACKGROUND_DARK if is_dark else Colors.BACKGROUND_LIGHT,
    )
    
    # Exponer función de refresh
    container.refresh = cargar_medidores
    
    # Cargar datos iniciales
    cargar_medidores()
    
    return container


# Alias para compatibilidad
MedidoresView = create_medidores_view
