"""Índice del RAG: fragmentos de las reglas del repo y de la documentación
aprobada, con búsqueda por similitud de embeddings."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from ..perfil import Perfil

AQUI = Path(__file__).resolve().parent
FUENTES = AQUI / "fuentes"
CACHE = AQUI / ".indice"
MAX_CARACTERES = 1500

_ENCABEZADO = re.compile(r"^(#{1,4})\s+(.*)$")
_ID_REGLA = re.compile(r"^(R\d+)\.")


@dataclass(frozen=True)
class Fragmento:
    id: str
    origen: str  # "reglas" | "docs"
    fuente: str
    titulo: str
    texto: str


def _trozos(texto: str) -> list[str]:
    if len(texto) <= MAX_CARACTERES:
        return [texto]
    trozos, actual = [], ""
    for parrafo in texto.split("\n\n"):
        if actual and len(actual) + len(parrafo) > MAX_CARACTERES:
            trozos.append(actual.strip())
            actual = ""
        actual += parrafo + "\n\n"
    if actual.strip():
        trozos.append(actual.strip())
    return [t[:MAX_CARACTERES] for t in trozos]


def partir_markdown(texto: str, fuente: str, origen: str, prefijo: str) -> list[Fragmento]:
    """Un fragmento por sección. Una regla titulada «R7. ...» conserva R7 como id."""
    secciones: list[tuple[str, list[str]]] = [("", [])]
    en_bloque_de_codigo = False
    for linea in texto.splitlines():
        if linea.lstrip().startswith("```"):
            en_bloque_de_codigo = not en_bloque_de_codigo
        coincide = None if en_bloque_de_codigo else _ENCABEZADO.match(linea)
        if coincide:
            secciones.append((coincide.group(2).strip(), []))
        else:
            secciones[-1][1].append(linea)

    fragmentos: list[Fragmento] = []
    for titulo, lineas in secciones:
        cuerpo = "\n".join(lineas).strip()
        if not cuerpo:
            continue
        regla = _ID_REGLA.match(titulo)
        for trozo in _trozos(cuerpo):
            numero = len(fragmentos) + 1
            identificador = regla.group(1) if regla else f"{prefijo}#{numero}"
            if any(f.id == identificador for f in fragmentos):
                identificador = f"{identificador}-{numero}"
            contenido = f"{titulo}\n{trozo}" if titulo else trozo
            fragmentos.append(Fragmento(identificador, origen, fuente, titulo, contenido))
    return fragmentos


def recolectar(perfil: Perfil, con_docs: bool = True) -> list[Fragmento]:
    fragmentos: list[Fragmento] = []
    for ruta in perfil.archivos_de_reglas():
        relativa = ruta.relative_to(perfil.raiz).as_posix()
        fragmentos += partir_markdown(
            ruta.read_text(encoding="utf-8"), relativa, "reglas", ruta.stem
        )
    if con_docs and FUENTES.exists():
        for ruta in sorted(FUENTES.glob("*.md")):
            fragmentos += partir_markdown(
                ruta.read_text(encoding="utf-8"), f"docs/{ruta.name}", "docs", ruta.stem
            )
    return fragmentos


class Indice:
    def __init__(self, fragmentos: list[Fragmento], vectores: np.ndarray, embeddings):
        self.fragmentos = fragmentos
        self._embeddings = embeddings
        normas = np.linalg.norm(vectores, axis=1, keepdims=True)
        self._vectores = vectores / np.where(normas == 0, 1, normas)

    def tiene(self, identificador: str) -> bool:
        return any(f.id == identificador for f in self.fragmentos)

    def buscar(self, pregunta: str, k: int) -> list[tuple[Fragmento, float]]:
        consulta = np.asarray(self._embeddings.embed_query(pregunta), dtype=float)
        consulta = consulta / (np.linalg.norm(consulta) or 1)
        similitudes = self._vectores @ consulta
        mejores = np.argsort(-similitudes)[:k]
        return [(self.fragmentos[i], float(similitudes[i])) for i in mejores]


def construir_indice(perfil: Perfil, embeddings, con_docs: bool = True, cache: bool = True) -> Indice:
    fragmentos = recolectar(perfil, con_docs)
    textos = [f.texto for f in fragmentos]
    modelo = getattr(embeddings, "model", type(embeddings).__name__)
    huella = hashlib.sha256(json.dumps([modelo, textos]).encode("utf-8")).hexdigest()[:16]
    archivo = CACHE / f"{huella}.npy"
    if cache and archivo.exists():
        vectores = np.load(archivo)
    else:
        vectores = np.asarray(embeddings.embed_documents(textos), dtype=float)
        if cache:
            CACHE.mkdir(exist_ok=True)
            np.save(archivo, vectores)
            (CACHE / f"{huella}.json").write_text(
                json.dumps([asdict(f) for f in fragmentos], ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
    return Indice(fragmentos, vectores, embeddings)
