"""Perfil del repositorio revisado: todo lo que depende de ese repo."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path


@dataclass(frozen=True)
class Perfil:
    raiz: Path
    checks: dict[str, str]
    codigo: tuple[str, ...]
    ignorar: tuple[str, ...]
    reglas: tuple[str, ...]
    particion: str

    def ignorado(self, ruta: Path) -> bool:
        relativa = "/" + ruta.relative_to(self.raiz).as_posix()
        return any(fnmatch(relativa, patron) for patron in self.ignorar)

    def archivos_de_codigo(self) -> list[Path]:
        encontrados: set[Path] = set()
        for patron in self.codigo:
            encontrados.update(r for r in self.raiz.glob(patron) if r.is_file())
        return sorted(r for r in encontrados if not self.ignorado(r))

    def archivos_de_reglas(self) -> list[Path]:
        encontrados: set[Path] = set()
        for patron in self.reglas:
            encontrados.update(r for r in self.raiz.glob(patron) if r.is_file())
        return sorted(encontrados)


def cargar_perfil(raiz_repo: str | Path, archivo: str = "perfil.toml") -> Perfil:
    raiz = Path(raiz_repo).resolve()
    datos = tomllib.loads((raiz / archivo).read_text(encoding="utf-8"))
    return Perfil(
        raiz=raiz,
        checks=dict(datos["checks"]),
        codigo=tuple(datos["archivos"]["codigo"]),
        ignorar=tuple(datos["archivos"].get("ignorar", [])),
        reglas=tuple(datos["reglas"]["rutas"]),
        particion=datos.get("particion", {}).get("codigo", "lineas"),
    )
