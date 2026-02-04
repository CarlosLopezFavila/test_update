import flet as ft
import requests
import os
import sys
import tempfile
import subprocess
from pathlib import Path
import zipfile as zf
from packaging import version


OWNER = "CarlosLopezFavila"
REPO = "test_update_exe"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
actual_version = "v0.0.0"

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
headers["Accept"] = "application/vnd.github+json"


def get_app_dir():
    """Directorio de la aplicación (donde está main o main.py)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).parent.resolve()


def get_updater_cmd(app_dir: Path, staging_content_root: str):
    """Comando para ejecutar el updater (script o ejecutable)."""
    if getattr(sys, "frozen", False):
        updater_exe = app_dir / "updater"
        return [str(updater_exe), staging_content_root, str(app_dir)]
    updater_script = app_dir / "updater.py"
    return [sys.executable, str(updater_script), staging_content_root, str(app_dir)]


def check_version():
    """
    Comprueba si hay una versión más reciente en GitHub.
    Si la hay: descarga el zip a un directorio temporal, descomprime
    y devuelve la ruta al contenido (carpeta con main, etc.) para el updater.
    Si no hay actualización, devuelve None.
    """
    try:
        release_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
        release_resp = requests.get(release_url, headers=headers, timeout=15)
        release_resp.raise_for_status()
        release = release_resp.json()
    except Exception as e:
        print(f"No se pudo comprobar la versión: {e}")
        return None

    remote_version = release["tag_name"]
    zip_url = release["zipball_url"]

    if actual_version == remote_version:
        print("Versiones iguales, no hay actualización.")
        return None
    if version.parse(actual_version) >= version.parse(remote_version):
        return None

    print("Hay una actualización disponible:", remote_version)
    staging_base = Path(tempfile.mkdtemp(prefix=f"{REPO}_update_"))

    # Opción 1: Si el release tiene assets "main" (y opcionalmente "updater"), usarlos
    # (recomendado para Raspberry Pi: sube los binarios compilados como assets del release)
    assets = release.get("assets") or []
    main_asset = next((a for a in assets if a.get("name") == "main"), None)
    if main_asset:
        print("Descargando ejecutable desde assets...")
        try:
            r = requests.get(main_asset["browser_download_url"], headers=headers, timeout=120)
            r.raise_for_status()
            (staging_base / "main").write_bytes(r.content)
            os.chmod(staging_base / "main", 0o755)
        except Exception as e:
            print(f"Error al descargar main: {e}")
            return None
        updater_asset = next((a for a in assets if a.get("name") == "updater"), None)
        if updater_asset:
            try:
                r = requests.get(updater_asset["browser_download_url"], headers=headers, timeout=60)
                r.raise_for_status()
                (staging_base / "updater").write_bytes(r.content)
                os.chmod(staging_base / "updater", 0o755)
            except Exception as e:
                print(f"Advertencia: no se pudo descargar updater: {e}")
        print("Descarga lista.")
        return str(staging_base.resolve())

    # Opción 2: Descargar zipball (código fuente; debe incluir "main" y "updater" si son binarios)
    print(f"Descargando {zip_url} ...")
    try:
        response = requests.get(zip_url, headers=headers, timeout=60)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al descargar: {e}")
        return None

    zip_path = staging_base / f"{REPO}-{remote_version}.zip"
    try:
        zip_path.write_bytes(response.content)
    except Exception as e:
        print(f"Error al guardar zip: {e}")
        return None

    with zf.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(staging_base)

    subdirs = [d for d in staging_base.iterdir() if d.is_dir()]
    if not subdirs:
        print("Error: el zip no contiene una carpeta raíz.")
        return None
    content_root = str(subdirs[0].resolve())
    print("Archivos descomprimidos en:", content_root)
    return content_root


async def main(page: ft.Page):
    page.title = "Interfaz básica con Flet"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.bgcolor = ft.Colors.RED_100

    app_dir = get_app_dir()
    staging_content_root = check_version()

    if staging_content_root:
        # Hay actualización descargada: lanzar updater y cerrar esta instancia
        updater_cmd = get_updater_cmd(app_dir, staging_content_root)
        try:
            subprocess.Popen(
                updater_cmd,
                cwd=str(app_dir),
                start_new_session=True,
            )
        except Exception as e:
            print(f"Error al lanzar el updater: {e}")
        await page.window.close()
        os._exit(0)  # Salida directa: no lanza excepción en la tarea de Flet
        return

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

