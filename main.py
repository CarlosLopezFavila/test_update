import flet as ft
import requests
from pathlib import Path
import zipfile as zf
from get_tag_info import tag_name as remote_version, OWNER, REPO, GITHUB_TOKEN


global actual_version 
actual_version = "v1.0.3"


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

            base_path = Path(__file__).parent

            with zf.ZipFile(zip_filename, "r") as zip_ref:
                for member in zip_ref.infolist():
                    member_path = Path(member.filename)

                    # Ignorar la carpeta raíz (test_update-1.0.1/)
                    if len(member_path.parts) <= 1:
                        continue

                    # Quitar la carpeta raíz
                    relative_path = Path(*member_path.parts[1:])
                    target_path = base_path / relative_path

                    if member.is_dir():
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())

            print("Archivos descomprimidos")            
            

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
