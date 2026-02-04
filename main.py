import flet as ft
import os
import sys

from updater import check_update_available, run_update


async def main(page: ft.Page):
    page.title = "Interfaz básica con Flet"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.bgcolor = ft.Colors.RED_100

    # Solo detectar si hay actualización; no descargar aún
    hay_actualizacion, version_remota = check_update_available()

    texto = ft.Text(
        "Hola 👋 Esta es una interfaz básica con Flet",
        size=20
    )

    def boton_click(e):
        texto.value = "¡Botón presionado!"
        page.update()

    async def aplicar_actualizacion_click(e):
        if run_update():
            await page.window.close()
            os._exit(0)

    boton = ft.Button(
        "Presióname",
        on_click=boton_click
    )

    controles = [texto, boton]

    if hay_actualizacion:
        aviso = ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"Actualización disponible: {version_remota}", size=14, color=ft.Colors.GREEN_800),
                    ft.ElevatedButton(
                        "Actualizar ahora",
                        on_click=aplicar_actualizacion_click,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            bgcolor=ft.Colors.GREEN_100,
            padding=12,
            border_radius=8,
        )
        controles.insert(0, aviso)

    page.add(
        ft.Column(
            controls=controles,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )


ft.run(main)
