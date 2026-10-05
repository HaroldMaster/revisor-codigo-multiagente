"""Los sistemas que se pueden correr y medir, por nombre."""

from functools import partial

from .baseline import RevisorUnico, RevisorUnicoConPistas
from .config import get_llm
from .multiagente import RevisorMultiagente, SinRAG, SinVerificador


def _con_razonamiento_alto(clase, nombre: str):
    """Extensión: el mismo sistema, pidiéndole al modelo que razone más."""

    class ConRazonamientoAlto(clase):
        def __init__(self, **opciones):
            super().__init__(llm_de=partial(get_llm, esfuerzo="high"), **opciones)

    ConRazonamientoAlto.nombre = nombre
    return ConRazonamientoAlto


SISTEMAS = {
    "baseline": RevisorUnico,
    "baseline_con_pistas": RevisorUnicoConPistas,
    "multiagente": RevisorMultiagente,
    "sin_verificador": SinVerificador,
    "sin_rag": SinRAG,
    "baseline_razonamiento_alto": _con_razonamiento_alto(RevisorUnico, "baseline_razonamiento_alto"),
    "multiagente_razonamiento_alto": _con_razonamiento_alto(
        RevisorMultiagente, "multiagente_razonamiento_alto"
    ),
}
