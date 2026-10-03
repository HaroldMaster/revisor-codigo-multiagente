"""Copia limpia del repo revisado para aplicarle un parche sin tocar el original."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPO_PRUEBA = RAIZ / "repo-prueba"


@contextmanager
def repo_con_parches(*parches: Path, origen: Path = REPO_PRUEBA):
    """Entrega la ruta de una copia temporal con los parches aplicados en orden.
    Las dependencias instaladas no se copian: se enlazan."""
    carpeta = Path(tempfile.mkdtemp(prefix="revisor-"))
    copia = carpeta / origen.name
    try:
        shutil.copytree(origen, copia, ignore=shutil.ignore_patterns("node_modules", "dist"))
        dependencias = origen / "node_modules"
        if dependencias.exists():
            (copia / "node_modules").symlink_to(dependencias)
        for parche in parches:
            subprocess.run(
                ["git", "apply", "--whitespace=nowarn", str(Path(parche).resolve())],
                cwd=copia,
                check=True,
                capture_output=True,
                text=True,
            )
        yield copia
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
