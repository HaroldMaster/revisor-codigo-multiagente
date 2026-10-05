"""Redacta el informe y comprueba en código que no añadió nada."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..contexto import Contexto
from ..estado import Hallazgo
from ..frenos import PresupuestoAgotado
from ..informe import redactar
from ..llamada import invocar, texto_de
from .prompts import SINTETIZADOR

_UBICACION = re.compile(r"([\w./-]+\.[a-zA-Z]{1,4}):(\d+)")
_REGLA = re.compile(r"\bR\d+\b")


def sin_procedencia(informe: str, hallazgos: list[Hallazgo]) -> list[str]:
    """Ubicaciones y reglas que el informe menciona y que no vienen de ningún hallazgo."""
    ubicaciones = {(h.archivo, h.linea) for h in hallazgos}
    reglas = {h.cita_regla for h in hallazgos if h.cita_regla}
    ajenas = [
        f"{archivo}:{linea}"
        for archivo, linea in _UBICACION.findall(informe)
        if (archivo, int(linea)) not in ubicaciones
    ]
    ajenas += [regla for regla in _REGLA.findall(informe) if regla not in reglas]
    return sorted(set(ajenas))


def sintetizar(hallazgos: list[Hallazgo], avisos: list[str], contexto: Contexto) -> str:
    vigentes = [h for h in hallazgos if h.veredicto != "descartado"]
    if not vigentes:
        return redactar([], avisos)
    datos = json.dumps([h.model_dump(exclude={"origen", "id"}) for h in vigentes], ensure_ascii=False, indent=1)
    mensajes = [SystemMessage(SINTETIZADOR), HumanMessage(f"Hallazgos verificados:\n{datos}")]
    for _ in range(2):
        try:
            respuesta = invocar(
                contexto.llm_de("sintetizador"), mensajes, agente="sintetizador",
                modelo=contexto.modelo_de("sintetizador"), traza=contexto.traza, con_reserva=True,
            )
        except PresupuestoAgotado:
            break
        informe = texto_de(respuesta).strip()
        ajenas = sin_procedencia(informe, vigentes)
        if informe and not ajenas:
            return "\n\n".join([*(f"> {a}" for a in avisos), informe])
        contexto.traza.evento("procedencia", rechazado=ajenas or ["informe vacío"])
        mensajes += [
            respuesta,
            HumanMessage(
                f"El informe menciona cosas que no están en la lista: {ajenas}. "
                "Reescríbelo usando solo las ubicaciones y reglas de los hallazgos."
            ),
        ]
    # El modelo no logró un informe fiel: se entrega el que arma el código.
    contexto.traza.evento("procedencia", rechazado=["se usa el informe generado por código"])
    return redactar(vigentes, avisos)
