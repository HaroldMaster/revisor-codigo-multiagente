"""Lo que comparte una corrida: el repo, el índice, la traza y cómo pedir un modelo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .config import get_llm, id_modelo
from .perfil import Perfil
from .rag.indice import Indice
from .traza import Traza


@dataclass
class Contexto:
    perfil: Perfil
    indice: Indice | None
    traza: Traza
    llm_de: Callable[[str], object] = get_llm
    modelo_de: Callable[[str], str] = id_modelo
    citas_devueltas: set[str] = field(default_factory=set)
    max_pasos: int = 12
