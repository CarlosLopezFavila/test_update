import requests
from packaging import version
import os

OWNER = "CarlosLopezFavila"
REPO = "test_update"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

# 1️⃣ Obtener todos los tags
tags_url = f"https://api.github.com/repos/{OWNER}/{REPO}/tags"
tags_resp = requests.get(tags_url, headers=headers)
tags_resp.raise_for_status()
tags = tags_resp.json()

if not tags:
    raise RuntimeError("No hay tags en el repositorio")

# 2️⃣ Ordenar por versión semántica y tomar el último
latest = max(tags, key=lambda t: version.parse(t["name"].lstrip("v")))
tag_name = latest["name"]
print(type(tag_name))
print(tag_name)
commit_sha = latest["commit"]["sha"]

# 3️⃣ Obtener info del commit
commit_url = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{commit_sha}"
commit_resp = requests.get(commit_url, headers=headers)
commit_resp.raise_for_status()
commit = commit_resp.json()
"""
print("🏷️ Último tag publicado")
print(f"Tag: {tag_name}")
print(f"Commit SHA: {commit_sha}")
print(f"Autor: {commit['commit']['author']['name']}")
print(f"Email: {commit['commit']['author']['email']}")
print(f"Fecha: {commit['commit']['author']['date']}")
print(f"Mensaje: {commit['commit']['message']}")
print(f"URL: {commit['html_url']}")"""
