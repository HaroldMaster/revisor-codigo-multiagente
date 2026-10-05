"""Los sistemas que se pueden correr y medir, por nombre."""

from functools import partial

from .baseline import RevisorUnico, RevisorUnicoConPistas
from .config import get_llm
from .multiagente import RevisorMultiagente, SinRAG, SinVerificador


def _con_razonamiento(clase, nombre: str, esfuerzo: str):
    """Extensión: el mismo sistema, pidiéndole al modelo que razone más."""

    class ConOtroRazonamiento(clase):
        def __init__(self, **opciones):
            super().__init__(llm_de=partial(get_llm, esfuerzo=esfuerzo), **opciones)

    ConOtroRazonamiento.nombre = nombre
    return ConOtroRazonamiento


SISTEMAS = {
    "baseline": RevisorUnico,
    "baseline_con_pistas": RevisorUnicoConPistas,
    "multiagente": RevisorMultiagente,
    "sin_verificador": SinVerificador,
    "sin_rag": SinRAG,
    "baseline_razonamiento_medio": _con_razonamiento(RevisorUnico, "baseline_razonamiento_medio", "medium"),
    "baseline_razonamiento_alto": _con_razonamiento(RevisorUnico, "baseline_razonamiento_alto", "high"),
    "multiagente_razonamiento_alto": _con_razonamiento(
        RevisorMultiagente, "multiagente_razonamiento_alto", "high"
    ),
}
