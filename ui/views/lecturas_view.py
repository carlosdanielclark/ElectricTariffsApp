"""
Electric Tariffs App - Vista de Lecturas
========================================
CRUD completo de lecturas con detección de rollover
y visualización de efecto dominó.
"""

import flet as ft
from datetime import date, datetime, timedelta
from typing import Optional, Callable, List

from core.models import Medidor, Lectura
from ui.viewmodels.lectura_viewmodel import LecturaViewModel
from ui.styles import (
    Colors, Sizes,
    get_input_style, get_button_style, get_card_style,
    show_snackbar,
)


def create_lecturas_view(
    page: ft.Page,
    medidor: Medidor,
    on_volver: Callable,
    is_dark: bool = True,
) -> ft.Container:
    """
    Crea la vista de lecturas para un medidor.
    
    Args:
        page: Página Flet
        medidor: Medidor seleccionado
        on_volver: Callback para volver a medidores
        is_dark: Si usa tema oscuro
        
    Returns:
        Container con la vista completa
    """
    vm = LecturaViewModel()
    
    # Estado local
    anio_actual = date.today().year
    anio_seleccionado = anio_actual
    lecturas_lista: List[Lectura] = []
    lectura_editando: Optional[Lectura] = None
    
    # =========================================================================
    # COMPONENTES UI
    # =========================================================================
    
    # Selector de año
    anios_disponibles = vm.obtener_anios_disponibles(medidor.id)
    dropdown_anio = ft.Dropdown(
        label="Año",
        value=str(anio_actual),
        options=[ft.dropdown.Option(str(a)) for a in anios_disponibles],
        width=120,
        on_change=lambda e: cargar_lecturas(int(e.control.value)),
    )
    
    # Tabla de lecturas
    tabla_lecturas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Período", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Anterior", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Actual", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Consumo", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Importe", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Rollover", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
        ],
        border=ft.border.all(1, Colors.BORDER_DARK if is_dark else Colors.BORDER_LIGHT),
        border_radius=Sizes.BORDER_RADIUS,
        heading_row_color=ft.Colors.with_opacity(0.1, Colors.PRIMARY),
        column_spacing=20,
    )
    
    # Mensaje vacío
    mensaje_vacio = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.RECEIPT_LONG_OUTLINED,
                    size=64,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    "No hay lecturas registradas",
                    size=16,
                    color=Colors.TEXT_SECONDARY,
                ),
                ft.Text(
                    "Usa el botón + para agregar la primera lectura",
                    size=14,
                    color=Colors.TEXT_SECONDARY,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        padding=40,
        visible=False,
    )
    
    # Contenedor de la tabla
    contenedor_tabla = ft.Container(
        content=ft.Column(
            controls=[tabla_lecturas],
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
    )
    
    # Resumen del medidor
    txt_total_lecturas = ft.Text("0 lecturas", size=14)
    txt_consumo_total = ft.Text("0 kWh", size=14, weight=ft.FontWeight.BOLD)
    txt_importe_total = ft.Text("$0 CUP", size=14, weight=ft.FontWeight.BOLD)
    
    resumen_card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Total Lecturas", size=12, color=Colors.TEXT_SECONDARY),
                            txt_total_lecturas,
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Consumo Total", size=12, color=Colors.TEXT_SECONDARY),
                            txt_consumo_total,
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                ft.VerticalDivider(width=1),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Importe Total", size=12, color=Colors.TEXT_SECONDARY),
                            txt_importe_total,
                        ],
                        spacing=4,
                    ),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=Sizes.PADDING_MD,
        bgcolor=Colors.SURFACE_DARK if is_dark else Colors.SURFACE_LIGHT,
        border_radius=Sizes.BORDER_RADIUS,
    )
    
    # =========================================================================
    # DIÁLOGO DE NUEVA/EDITAR LECTURA
    # =========================================================================
    
    # Campos del formulario
    txt_fecha_inicio = ft.TextField(
        label="Fecha Inicio",
        hint_text="YYYY-MM-DD",
        **get_input_style(is_dark),
        width=200,
    )
    
    txt_fecha_fin = ft.TextField(
        label="Fecha Fin",
        hint_text="YYYY-MM-DD",
        **get_input_style(is_dark),
        width=200,
    )
    
    txt_lectura_anterior = ft.TextField(
        label="Lectura Anterior",
        read_only=True,
        **get_input_style(is_dark),
        width=150,
    )
    
    txt_lectura_actual = ft.TextField(
        label="Lectura Actual",
        hint_text="Ej: 1234.5",
        **get_input_style(is_dark),
        width=150,
        keyboard_type=ft.KeyboardType.NUMBER,
    )
    
    txt_consumo_preview = ft.Text("Consumo: -- kWh", size=14)
    txt_importe_preview = ft.Text("Importe: $-- CUP", size=14, weight=ft.FontWeight.BOLD)
    txt_rollover_warning = ft.Text(
        "",
        size=12,
        color=Colors.WARNING,
        visible=False,
    )
    
    chk_confirmar_rollover = ft.Checkbox(
        label="Confirmar valor (rollover o corrección)",
        value=False,
        visible=False,
    )
    
    btn_precalcular = ft.ElevatedButton(
        text="Calcular",
        icon=ft.Icons.CALCULATE,
        on_click=lambda e: precalcular_lectura(),
    )
    
    dialogo_lectura = ft.AlertDialog(
        modal=True,
        title=ft.Text("Nueva Lectura"),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[txt_fecha_inicio, txt_fecha_fin],
                        spacing=16,
                    ),
                    ft.Divider(),
                    ft.Row(
                        controls=[txt_lectura_anterior, txt_lectura_actual],
                        spacing=16,
                    ),
                    ft.Row(
                        controls=[btn_precalcular],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Divider(),
                    txt_consumo_preview,
                    txt_importe_preview,
                    txt_rollover_warning,
                    chk_confirmar_rollover,
                ],
                spacing=12,
                tight=True,
            ),
            width=450,
            padding=Sizes.PADDING_MD,
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: cerrar_dialogo()),
            ft.ElevatedButton(
                "Guardar",
                icon=ft.Icons.SAVE,
                on_click=lambda e: guardar_lectura(),
                **get_button_style("primary"),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    # Diálogo de confirmación de eliminación
    dialogo_confirmar = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmar Eliminación"),
        content=ft.Text("¿Estás seguro de eliminar esta lectura? Esta acción no se puede deshacer."),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: cerrar_confirmar()),
            ft.ElevatedButton(
                "Eliminar",
                icon=ft.Icons.DELETE,
                bgcolor=Colors.ERROR,
                color=Colors.TEXT_DARK,
                on_click=lambda e: confirmar_eliminacion(),
            ),
        ],
    )
    
    lectura_a_eliminar: Optional[int] = None
    
    # =========================================================================
    # FUNCIONES
    # =========================================================================
    
    def cargar_lecturas(anio: Optional[int] = None) -> None:
        """Carga lecturas del medidor."""
        nonlocal lecturas_lista, anio_seleccionado
        
        if anio:
            anio_seleccionado = anio
        
        lecturas_lista = vm.obtener_lecturas_medidor(medidor.id, anio_seleccionado)
        actualizar_tabla()
        actualizar_resumen()
    
    def actualizar_tabla() -> None:
        """Actualiza la tabla de lecturas."""
        tabla_lecturas.rows.clear()
        
        if not lecturas_lista:
            mensaje_vacio.visible = True
            contenedor_tabla.visible = False
        else:
            mensaje_vacio.visible = False
            contenedor_tabla.visible = True
            
            for lectura in lecturas_lista:
                # Formatear período
                periodo = f"{lectura.fecha_inicio} a {lectura.fecha_fin}" if lectura.fecha_inicio else str(lectura.fecha_fin)
                
                # Verificar permisos
                puede_editar = vm.puede_editar_lectura(lectura)
                puede_eliminar = vm.puede_eliminar_lectura(lectura)
                
                # Acciones
                acciones = ft.Row(
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_size=18,
                            tooltip="Editar",
                            on_click=lambda e, l=lectura: abrir_edicion(l),
                            disabled=not puede_editar,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_size=18,
                            icon_color=Colors.ERROR if puede_eliminar else Colors.TEXT_SECONDARY,
                            tooltip="Eliminar",
                            on_click=lambda e, l=lectura: solicitar_eliminacion(l.id),
                            disabled=not puede_eliminar,
                        ),
                    ],
                    spacing=0,
                )
                
                tabla_lecturas.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(periodo, size=13)),
                            ft.DataCell(ft.Text(f"{lectura.lectura_anterior:.1f}", size=13)),
                            ft.DataCell(ft.Text(f"{lectura.lectura_actual:.1f}", size=13)),
                            ft.DataCell(ft.Text(f"{lectura.consumo_kwh:.1f} kWh", size=13)),
                            ft.DataCell(ft.Text(f"${round(lectura.importe_total)} CUP", size=13, weight=ft.FontWeight.BOLD)),
                            ft.DataCell(
                                ft.Icon(
                                    ft.Icons.REFRESH if lectura.es_rollover else ft.Icons.REMOVE,
                                    size=18,
                                    color=Colors.WARNING if lectura.es_rollover else Colors.TEXT_SECONDARY,
                                )
                            ),
                            ft.DataCell(acciones),
                        ],
                    )
                )
        
        page.update()
    
    def actualizar_resumen() -> None:
        """Actualiza el resumen del medidor."""
        resumen = vm.obtener_resumen_medidor(medidor.id)
        txt_total_lecturas.value = f"{resumen['total_lecturas']} lecturas"
        txt_consumo_total.value = f"{resumen['consumo_total']:.1f} kWh"
        txt_importe_total.value = f"${round(resumen['importe_total'])} CUP"
        page.update()
    
    def abrir_nueva_lectura() -> None:
        """Abre diálogo para nueva lectura."""
        nonlocal lectura_editando
        lectura_editando = None
        
        dialogo_lectura.title = ft.Text("Nueva Lectura")
        
        # Precargar datos
        ultima = vm.obtener_ultima_lectura(medidor.id)
        
        # Fechas por defecto
        hoy = date.today()
        if ultima and ultima.fecha_fin:
            fecha_inicio = ultima.fecha_fin + timedelta(days=1)
        else:
            fecha_inicio = hoy.replace(day=1)
        
        txt_fecha_inicio.value = fecha_inicio.isoformat()
        txt_fecha_fin.value = hoy.isoformat()
        txt_lectura_anterior.value = f"{ultima.lectura_actual:.1f}" if ultima else "0.0"
        txt_lectura_actual.value = ""
        txt_consumo_preview.value = "Consumo: -- kWh"
        txt_importe_preview.value = "Importe: $-- CUP"
        txt_rollover_warning.visible = False
        chk_confirmar_rollover.visible = False
        chk_confirmar_rollover.value = False
        
        page.overlay.append(dialogo_lectura)
        dialogo_lectura.open = True
        page.update()
    
    def abrir_edicion(lectura: Lectura) -> None:
        """Abre diálogo para editar lectura."""
        nonlocal lectura_editando
        lectura_editando = lectura
        
        dialogo_lectura.title = ft.Text("Editar Lectura")
        
        txt_fecha_inicio.value = lectura.fecha_inicio.isoformat() if lectura.fecha_inicio else ""
        txt_fecha_fin.value = lectura.fecha_fin.isoformat() if lectura.fecha_fin else ""
        txt_fecha_inicio.read_only = True
        txt_fecha_fin.read_only = True
        txt_lectura_anterior.value = f"{lectura.lectura_anterior:.1f}"
        txt_lectura_actual.value = f"{lectura.lectura_actual:.1f}"
        txt_consumo_preview.value = f"Consumo: {lectura.consumo_kwh:.1f} kWh"
        txt_importe_preview.value = f"Importe: ${round(lectura.importe_total)} CUP"
        txt_rollover_warning.visible = False
        chk_confirmar_rollover.visible = False
        chk_confirmar_rollover.value = False
        
        page.overlay.append(dialogo_lectura)
        dialogo_lectura.open = True
        page.update()
    
    def cerrar_dialogo() -> None:
        """Cierra el diálogo."""
        nonlocal lectura_editando
        lectura_editando = None
        txt_fecha_inicio.read_only = False
        txt_fecha_fin.read_only = False
        dialogo_lectura.open = False
        page.update()
    
    def precalcular_lectura() -> None:
        """Precalcula consumo e importe."""
        try:
            lectura_actual = float(txt_lectura_actual.value or 0)
            fecha_fin = date.fromisoformat(txt_fecha_fin.value)
        except (ValueError, TypeError):
            show_snackbar(page, "Valores inválidos", "error")
            return
        
        exito, mensaje, datos = vm.precalcular_lectura(
            medidor.id,
            lectura_actual,
            fecha_fin,
            chk_confirmar_rollover.value
        )
        
        if datos:
            txt_lectura_anterior.value = f"{datos['lectura_anterior']:.1f}"
            txt_consumo_preview.value = f"Consumo: {datos['consumo']:.1f} kWh"
            txt_importe_preview.value = f"Importe: ${datos.get('importe_redondeado', 0)} CUP"
            
            if datos.get("requiere_confirmacion"):
                txt_rollover_warning.value = datos.get("mensaje_rollover", "Requiere confirmación")
                txt_rollover_warning.visible = True
                chk_confirmar_rollover.visible = True
            elif datos.get("es_rollover"):
                txt_rollover_warning.value = "⚠️ Rollover detectado automáticamente"
                txt_rollover_warning.visible = True
                chk_confirmar_rollover.visible = False
            else:
                txt_rollover_warning.visible = False
                chk_confirmar_rollover.visible = False
        else:
            txt_rollover_warning.value = mensaje
            txt_rollover_warning.visible = True
            chk_confirmar_rollover.visible = True
        
        page.update()
    
    def guardar_lectura() -> None:
        """Guarda la lectura (nueva o editada)."""
        try:
            lectura_actual = float(txt_lectura_actual.value or 0)
            fecha_inicio = date.fromisoformat(txt_fecha_inicio.value)
            fecha_fin = date.fromisoformat(txt_fecha_fin.value)
        except (ValueError, TypeError):
            show_snackbar(page, "Valores inválidos", "error")
            return
        
        if lectura_editando:
            # Actualizar
            exito, mensaje, alerta = vm.actualizar_lectura(
                lectura_editando.id,
                lectura_actual,
                chk_confirmar_rollover.value
            )
        else:
            # Crear
            exito, mensaje, lectura_creada, alerta = vm.crear_lectura(
                medidor.id,
                fecha_inicio,
                fecha_fin,
                lectura_actual,
                chk_confirmar_rollover.value
            )
        
        if exito:
            cerrar_dialogo()
            cargar_lecturas()
            show_snackbar(page, mensaje, "success")
            
            if alerta:
                show_snackbar(page, f"⚠️ {alerta}", "warning")
        else:
            show_snackbar(page, mensaje, "error")
    
    def solicitar_eliminacion(lectura_id: int) -> None:
        """Muestra diálogo de confirmación."""
        nonlocal lectura_a_eliminar
        lectura_a_eliminar = lectura_id
        
        page.overlay.append(dialogo_confirmar)
        dialogo_confirmar.open = True
        page.update()
    
    def cerrar_confirmar() -> None:
        """Cierra diálogo de confirmación."""
        dialogo_confirmar.open = False
        page.update()
    
    def confirmar_eliminacion() -> None:
        """Ejecuta la eliminación."""
        nonlocal lectura_a_eliminar
        
        if lectura_a_eliminar:
            exito, mensaje = vm.eliminar_lectura(lectura_a_eliminar)
            
            cerrar_confirmar()
            lectura_a_eliminar = None
            
            if exito:
                cargar_lecturas()
                show_snackbar(page, mensaje, "success")
            else:
                show_snackbar(page, mensaje, "error")
    
    # =========================================================================
    # LAYOUT
    # =========================================================================
    
    # Header
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda e: on_volver(),
                    tooltip="Volver",
                ),
                ft.Icon(ft.Icons.ELECTRIC_METER, size=32, color=Colors.PRIMARY),
                ft.Column(
                    controls=[
                        ft.Text(
                            medidor.etiqueta,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=Colors.TEXT_DARK if is_dark else Colors.TEXT_LIGHT,
                        ),
                        ft.Text(
                            f"Nº Serie: {medidor.numero_serie or 'N/A'}",
                            size=12,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                dropdown_anio,
                ft.FloatingActionButton(
                    icon=ft.Icons.ADD,
                    bgcolor=Colors.PRIMARY,
                    on_click=lambda e: abrir_nueva_lectura(),
                    tooltip="Nueva Lectura",
                    mini=True,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=Sizes.PADDING_MD,
    )
    
    # Contenido principal
    contenido = ft.Container(
        content=ft.Column(
            controls=[
                resumen_card,
                ft.Container(height=16),
                mensaje_vacio,
                contenedor_tabla,
            ],
            expand=True,
        ),
        padding=Sizes.PADDING_MD,
        expand=True,
    )
    
    # Cargar datos iniciales
    cargar_lecturas()
    
    return ft.Container(
        content=ft.Column(
            controls=[header, contenido],
            spacing=0,
            expand=True,
        ),
        expand=True,
        bgcolor=Colors.BACKGROUND_DARK if is_dark else Colors.BACKGROUND_LIGHT,
    )
