"""Descarga las fuentes aprobadas a revisor/rag/fuentes/ con su fecha.

El índice se construye sobre esta copia y nunca sobre la web en vivo:
dos corridas del golden set consultan exactamente los mismos documentos.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
import urllib.request
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LISTA = AQUI / "fuentes_aprobadas.toml"
DESTINO = AQUI / "fuentes"


def descargar() -> list[dict]:
    fuentes = tomllib.loads(LISTA.read_text(encoding="utf-8"))["fuente"]
    DESTINO.mkdir(exist_ok=True)
    registro = []
    for fuente in fuentes:
        with urllib.request.urlopen(fuente["url"], timeout=30) as respuesta:
            contenido = respuesta.read()
        (DESTINO / f"{fuente['id']}.md").write_bytes(contenido)
        registro.append(
            {
                "id": fuente["id"],
                "url": fuente["url"],
                "fecha": date.today().isoformat(),
                "bytes": len(contenido),
                "sha256": hashlib.sha256(contenido).hexdigest(),
            }
        )
    (DESTINO / "DESCARGA.json").write_text(
        json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return registro


if __name__ == "__main__":
    for fila in descargar():
        print(f"{fila['id']}: {fila['bytes']} bytes, {fila['fecha']}")
