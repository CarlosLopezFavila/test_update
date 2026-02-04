#!/usr/bin/env python3
"""
Módulo de actualización: detección de nuevas versiones y ejecución del update.
También puede ejecutarse como script independiente (reemplaza archivos y relanza main).

Funciones llamables desde main:
  - check_update_available() -> (bool, str): True si hay actualización y versión remota
  - run_update() -> bool: descarga, descomprime, lanza el updater y devuelve True; False si error

Uso como script: updater <staging_dir> <target_dir>
"""

import os
import sys
import time
import shutil
import tempfile
import subprocess
import zipfile as zf
from pathlib import Path

# requests y packaging solo se importan dentro de check_update_available y run_update
# para que el ejecutable "updater" (script) no los necesite y sea más pequeño

# Configuración del repo (compartida con main para la lógica de update)
OWNER = "CarlosLopezFavila"
REPO = "test_update_exe"
ACTUAL_VERSION = "v0.0.0"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
HEADERS["Accept"] = "application/vnd.github+json"


def _get_app_dir():
    """Directorio de la aplicación (donde está main o main.py)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    # Cuando se importa desde main.py
    return Path(__file__).parent.resolve()


def _get_updater_cmd(app_dir: Path, staging_content_root: str):
    """Comando para ejecutar el updater (script o ejecutable)."""
    if getattr(sys, "frozen", False):
        updater_exe = app_dir / "updater"
        return [str(updater_exe), staging_content_root, str(app_dir)]
    updater_script = app_dir / "updater.py"
    return [sys.executable, str(updater_script), staging_content_root, str(app_dir)]


def check_update_available(current_version: str | None = None) -> tuple[bool, str]:
    """
    Comprueba si hay una versión más reciente en GitHub.
    Llamable desde main para mostrar notificación en la interfaz.

    Returns:
        (True, versión_remota) si hay actualización disponible.
        (False, "") si no hay actualización o hay error.
    """
    try:
        import requests
        from packaging import version
    except ImportError:
        return False, ""
    ver = current_version or ACTUAL_VERSION
    try:
        release_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
        release_resp = requests.get(release_url, headers=HEADERS, timeout=15)
        release_resp.raise_for_status()
        release = release_resp.json()
    except Exception:
        return False, ""

    remote_version = release["tag_name"]
    if ver == remote_version:
        return False, ""
    if version.parse(ver) >= version.parse(remote_version):
        return False, ""
    return True, remote_version


def run_update(current_version: str | None = None) -> bool:
    """
    Descarga la actualización, descomprime y lanza el proceso updater.
    Llamable desde main cuando el usuario confirma la actualización.
    Después de llamar esto, main debe cerrar la ventana y salir (os._exit(0)).

    Returns:
        True si se lanzó el updater correctamente (la app debe cerrarse).
        False si hubo error (no se lanzó el updater).
    """
    try:
        import requests
        from packaging import version
    except ImportError:
        return False
    ver = current_version or ACTUAL_VERSION
    try:
        release_url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
        release_resp = requests.get(release_url, headers=HEADERS, timeout=15)
        release_resp.raise_for_status()
        release = release_resp.json()
    except Exception as e:
        print(f"No se pudo obtener el release: {e}")
        return False

    remote_version = release["tag_name"]
    zip_url = release["zipball_url"]
    if version.parse(ver) >= version.parse(remote_version):
        return False

    staging_base = Path(tempfile.mkdtemp(prefix=f"{REPO}_update_"))
    assets = release.get("assets") or []
    main_asset = next((a for a in assets if a.get("name") == "main"), None)

    if main_asset:
        try:
            r = requests.get(main_asset["browser_download_url"], headers=HEADERS, timeout=120)
            r.raise_for_status()
            (staging_base / "main").write_bytes(r.content)
            os.chmod(staging_base / "main", 0o755)
        except Exception as e:
            print(f"Error al descargar main: {e}")
            return False
        updater_asset = next((a for a in assets if a.get("name") == "updater"), None)
        if updater_asset:
            try:
                r = requests.get(updater_asset["browser_download_url"], headers=HEADERS, timeout=60)
                r.raise_for_status()
                (staging_base / "updater").write_bytes(r.content)
                os.chmod(staging_base / "updater", 0o755)
            except Exception:
                pass
        content_root = str(staging_base.resolve())
    else:
        try:
            response = requests.get(zip_url, headers=HEADERS, timeout=60)
            response.raise_for_status()
        except Exception as e:
            print(f"Error al descargar: {e}")
            return False
        zip_path = staging_base / f"{REPO}-{remote_version}.zip"
        try:
            zip_path.write_bytes(response.content)
        except Exception as e:
            print(f"Error al guardar zip: {e}")
            return False
        with zf.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(staging_base)
        subdirs = [d for d in staging_base.iterdir() if d.is_dir()]
        if not subdirs:
            print("Error: el zip no contiene una carpeta raíz.")
            return False
        content_root = str(subdirs[0].resolve())

    app_dir = _get_app_dir()
    updater_cmd = _get_updater_cmd(app_dir, content_root)
    try:
        subprocess.Popen(
            updater_cmd,
            cwd=str(app_dir),
            start_new_session=True,
        )
    except Exception as e:
        print(f"Error al lanzar el updater: {e}")
        return False
    return True


def main():
    if len(sys.argv) < 3:
        print("Uso: updater <staging_dir> <target_dir>", file=sys.stderr)
        sys.exit(1)

    staging_dir = Path(sys.argv[1]).resolve()
    target_dir = Path(sys.argv[2]).resolve()

    if not staging_dir.is_dir():
        print(f"Error: staging_dir no existe: {staging_dir}", file=sys.stderr)
        sys.exit(1)
    if not target_dir.is_dir():
        print(f"Error: target_dir no existe: {target_dir}", file=sys.stderr)
        sys.exit(1)

    # Dar tiempo a que la aplicación principal termine y suelte el ejecutable
    time.sleep(2)

    # Copiar todo de staging a target (sobrescribir)
    for item in staging_dir.rglob("*"):
        rel = item.relative_to(staging_dir)
        dest = target_dir / rel
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            # Ejecutables: asegurar permisos en Linux
            if os.access(item, os.X_OK):
                os.chmod(dest, 0o755)

    # Nombre del ejecutable principal (mismo que en main.spec)
    main_name = "main"
    main_path = target_dir / main_name

    if not main_path.exists():
        print(f"Error: no se encontró {main_path} después de copiar", file=sys.stderr)
        sys.exit(1)

    os.chmod(main_path, 0o755)

    # Eliminar el .zip descargado (está en el directorio padre del contenido)
    for f in staging_dir.parent.glob("*.zip"):
        try:
            f.unlink()
        except OSError:
            pass
    # Eliminar la carpeta de staging ya usada
    try:
        shutil.rmtree(staging_dir, ignore_errors=True)
    except OSError:
        pass

    # Relanzar la aplicación (reemplazar este proceso)
    os.execv(str(main_path), [str(main_path)])


if __name__ == "__main__":
    main()
