"""Los sistemas que se pueden correr y medir, por nombre."""

from .baseline import RevisorUnico
from .multiagente import RevisorMultiagente, SinRAG, SinVerificador

SISTEMAS = {
    "baseline": RevisorUnico,
    "multiagente": RevisorMultiagente,
    "sin_verificador": SinVerificador,
    "sin_rag": SinRAG,
}
