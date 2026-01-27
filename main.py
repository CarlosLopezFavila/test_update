import flet as ft
import requests
from get_tag_info import tag_name as remote_version, OWNER, REPO, GITHUB_TOKEN


global actual_version 
actual_version = "v1.0.1"
def check_version():
    if actual_version != remote_version:
        print("Diferentes Versiones")
        number_remote_version = remote_version[1:]
        number_local_version = actual_version[1:]
        if number_local_version < number_remote_version:
            headers = {}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"

            print("Es necesario decargar la ultima actualización")
            # 4️⃣ Descargar el zip del último tag
            zip_url = f"https://github.com/{OWNER}/{REPO}/archive/refs/tags/{remote_version}.zip"
            print(f"Descargando {zip_url} ...")

            response = requests.get(zip_url, headers=headers)
            response.raise_for_status()

            zip_filename = f"{REPO}-{remote_version}.zip"
            with open(zip_filename, "wb") as f:
                f.write(response.content)

            print(f"Archivo descargado: {zip_filename}")
    else:
        print("versiones iguales")


def main(page: ft.Page):
    page.title = "Interfaz básica con Flet"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.bgcolor = ft.Colors.RED_100

    check_version()

    texto = ft.Text(
        "Hola 👋 Esta es una interfaz básica con Flet",
        size=20
    )

    def boton_click(e):
        texto.value = "¡Botón presionado!"
        page.update()

    boton = ft.Button(
        "Presióname",
        on_click=boton_click
    )

    page.add(
        ft.Column(
            controls=[texto, boton],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

# 👉 NUEVA forma correcta
ft.run(main)
