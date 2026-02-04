#!/usr/bin/env python3
"""
Updater independiente: reemplaza los archivos de la app con los descargados
y vuelve a lanzar el ejecutable principal.
Debe ejecutarse como proceso separado (la app principal ya cerró).

Uso: updater <staging_dir> <target_dir>
  staging_dir: carpeta con los archivos nuevos (descomprimidos)
  target_dir: carpeta donde está la app actual (main, updater, etc.)
"""

import os
import sys
import time
import shutil
from pathlib import Path


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
