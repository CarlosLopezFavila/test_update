import flet as ft
import requests, os
from pathlib import Path
import zipfile as zf
from packaging import version


OWNER = "CarlosLopezFavila"
REPO = "test_update_exe"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ===================OBTIENE INFO DE ULTIMO RELEASE  ==========================
global headers
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

# Obtener último release
release_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
release_resp = requests.get(release_url, headers=headers)
release_resp.raise_for_status()
release = release_resp.json()

remote_version = release["tag_name"]
zip_url = release["zipball_url"]


global actual_version 
actual_version = "v0.0.0"


def check_version():
    if actual_version != remote_version:
        print("Diferentes Versiones")
        if version.parse(actual_version) < version.parse(remote_version):

            print("Es necesario decargar la ultima actualización")
            # 4️⃣ Descargar el zip del último tag
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

