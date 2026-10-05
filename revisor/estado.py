"""La libreta compartida del grafo y la ficha de hallazgo."""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field

Dimension = Literal["correctness", "reglas", "clean_code", "eficiencia", "impacto"]
Severidad = Literal["critico", "alto", "medio"]
Veredicto = Literal["pendiente", "confirmado", "plausible", "descartado"]


class Hallazgo(BaseModel):
    id: str = ""
    origen: Literal["reviewer", "externo"] = "reviewer"
    dimension: Dimension
    archivo: str = Field(description="Ruta relativa a la raíz del repo")
    linea: int = Field(description="Línea del archivo donde está el problema")
    severidad: Severidad
    afirmacion: str = Field(description="Qué está mal, en una frase")
    evidencia: str = Field(description="Copia literal de la línea de código señalada")
    cita_regla: str | None = Field(
        default=None, description="Id del fragmento devuelto por buscar_reglas, si aplica"
    )
    veredicto: Veredicto = "pendiente"
    motivo_veredicto: str | None = None


class Estado(TypedDict, total=False):
    diff: str
    archivos: list[str]
    candidatos: Annotated[list[Hallazgo], operator.add]  # los reviewers escriben en paralelo
    hallazgos: list[Hallazgo]
    informe: str | None
    avisos: Annotated[list[str], operator.add]
    # capa 2
    comentarios: list
    respuestas: list
    # capa 3
    ticket: dict | None
    plan: dict | None
    intentos: int
