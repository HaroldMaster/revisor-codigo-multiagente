"""Verificación de hallazgos: primero el código, después un modelo.

Lo que se puede comprobar sin modelo (la línea existe, la evidencia es
literal, la cita de regla salió del RAG en esta corrida) no se le pregunta a
un modelo. Solo lo que pasa ese filtro llega al verificador.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..contexto import Contexto
from ..estado import Hallazgo
from ..llamada import invocar_estructurado
from .bucle import ejecutar_agente
from .prompts import VERIFICADOR, VERIFICADOR_HERRAMIENTAS

SEVERIDAD = {"critico": 0, "alto": 1, "medio": 2}
LARGO_MINIMO_EVIDENCIA = 8
MAX_PASOS_VERIFICADOR = 6


def _normal(texto: str) -> str:
    return " ".join(texto.split())


def unir(candidatos: list[Hallazgo]) -> list[Hallazgo]:
    """Dos hallazgos son el mismo si señalan el mismo archivo, la misma línea y la
    misma dimensión. Se conserva el que cita una regla y, a igualdad, el más severo.

    La dimensión forma parte de la clave a propósito: una misma línea puede tener un
    problema de eficiencia y otro de reglas, y unirlos pierde uno de los dos."""
    def prioridad(h: Hallazgo) -> tuple:
        return (h.cita_regla is None, SEVERIDAD[h.severidad])

    unidos: dict[tuple, Hallazgo] = {}
    for hallazgo in sorted(candidatos, key=prioridad):
        unidos.setdefault((hallazgo.archivo, hallazgo.linea, hallazgo.dimension), hallazgo)
    return sorted(unidos.values(), key=lambda h: (h.archivo, h.linea, h.dimension))


def comprobar_en_codigo(hallazgo: Hallazgo, contexto: Contexto, exigir_cita: bool = True) -> Hallazgo:
    """Devuelve el hallazgo, descartado si no supera las comprobaciones sin modelo."""
    def descartar(motivo: str) -> Hallazgo:
        return hallazgo.model_copy(update={"veredicto": "descartado", "motivo_veredicto": motivo})

    perfil = contexto.perfil
    archivo = (perfil.raiz / hallazgo.archivo).resolve()
    if not archivo.is_relative_to(perfil.raiz) or not archivo.is_file() or perfil.ignorado(archivo):
        return descartar(f"Comprobación en código: el archivo {hallazgo.archivo} no existe en el repositorio")

    evidencia = next((_normal(l) for l in hallazgo.evidencia.splitlines() if l.strip()), "")
    if len(evidencia) < LARGO_MINIMO_EVIDENCIA:
        return descartar("Comprobación en código: la evidencia está vacía o es demasiado corta")
    lineas = archivo.read_text(encoding="utf-8", errors="replace").splitlines()
    donde = [n for n, linea in enumerate(lineas, start=1) if evidencia in _normal(linea)]
    if not donde:
        return descartar("Comprobación en código: la evidencia no es una copia literal de ninguna línea del archivo")
    cambios: dict = {"linea": min(donde, key=lambda n: abs(n - hallazgo.linea))}

    if hallazgo.cita_regla and hallazgo.cita_regla not in contexto.citas_devueltas:
        if exigir_cita and hallazgo.dimension == "reglas":
            return descartar(
                f"Comprobación en código: la regla {hallazgo.cita_regla} no fue devuelta por buscar_reglas en esta corrida"
            )
        cambios["cita_regla"] = None
    return hallazgo.model_copy(update=cambios)


class Veredicto(BaseModel):
    veredicto: Literal["confirmado", "plausible", "descartado"]
    motivo: str = Field(description="Qué comprobaste y qué viste, en una o dos frases")


def verificar_con_modelo(hallazgo: Hallazgo, diff: str, contexto: Contexto) -> Hallazgo:
    ficha = hallazgo.model_dump_json(include={"dimension", "archivo", "linea", "afirmacion", "evidencia", "cita_regla"})
    tarea = (
        f"Hallazgo propuesto:\n{ficha}\n\n"
        f"Diff del cambio, ya aplicado al repositorio:\n```diff\n{diff}\n```\n\n"
        "Compruébalo con las herramientas y después da tu veredicto."
    )
    final = ejecutar_agente(
        "verificador", VERIFICADOR, tarea, VERIFICADOR_HERRAMIENTAS, contexto, "verificador",
        MAX_PASOS_VERIFICADOR,
    )
    decision = invocar_estructurado(
        contexto.llm_de("verificador"),
        Veredicto,
        [SystemMessage(VERIFICADOR), *final["messages"], HumanMessage("Da tu veredicto sobre el hallazgo.")],
        agente="verificador",
        modelo=contexto.modelo_de("verificador"),
        traza=contexto.traza,
    )
    if decision is None:
        return hallazgo.model_copy(
            update={"veredicto": "plausible", "motivo_veredicto": "El verificador no entregó un veredicto"}
        )
    return hallazgo.model_copy(update={"veredicto": decision.veredicto, "motivo_veredicto": decision.motivo})
