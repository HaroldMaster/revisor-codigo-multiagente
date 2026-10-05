"""Un reviewer: corre el bucle con su prompt y entrega fichas de hallazgo."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..contexto import Contexto
from ..estado import Dimension, Hallazgo, Severidad
from ..frenos import PresupuestoAgotado
from ..llamada import invocar_estructurado
from .bucle import ejecutar_agente
from .prompts import EXTRAER_SIN_RAG_NOTA


class HallazgoPropuesto(BaseModel):
    dimension: Dimension
    archivo: str = Field(description="Ruta relativa a la raíz del repo, tal como la devuelve leer_archivo")
    linea: int = Field(description="Número de línea en el archivo actual, no en el diff")
    severidad: Severidad
    afirmacion: str = Field(description="Qué está mal y por qué, en una o dos frases")
    evidencia: str = Field(description="Copia literal y completa de la línea señalada")
    cita_regla: str | None = Field(
        default=None,
        description="Id exacto de un fragmento devuelto por buscar_reglas (por ejemplo R12). Vacío si no aplica",
    )


class ListaDeHallazgos(BaseModel):
    hallazgos: list[HallazgoPropuesto]


EXTRAER = """Ahora entrega tus hallazgos en la lista estructurada.

- Incluye solo problemas que introduce o deja el diff y que sostuviste con lo que leíste.
- `linea` y `evidencia` salen de leer_archivo sobre el archivo actual; no las reconstruyas de memoria.
- `cita_regla` solo puede ser un id que te devolvió buscar_reglas.
- Si el cambio está bien, devuelve la lista vacía. No rellenes."""


def revisar(
    nombre: str,
    sistema: str,
    diff: str,
    herramientas: list[str],
    contexto: Contexto,
    rol: str = "reviewer",
    max_pasos: int | None = None,
) -> tuple[list[Hallazgo], str | None]:
    tarea = f"Revisa este diff. Los archivos del repositorio ya tienen el cambio aplicado.\n\n```diff\n{diff}\n```"
    final = ejecutar_agente(nombre, sistema, tarea, herramientas, contexto, rol, max_pasos)
    extraer = EXTRAER
    if "buscar_reglas" not in herramientas:
        extraer = EXTRAER.replace(
            "- `cita_regla` solo puede ser un id que te devolvió buscar_reglas.", EXTRAER_SIN_RAG_NOTA
        )
    try:
        # Paso de cierre: puede usar la reserva, para entregar lo que el agente
        # alcanzó a ver aunque un freno lo haya cortado.
        lista = invocar_estructurado(
            contexto.llm_de(rol),
            ListaDeHallazgos,
            [SystemMessage(sistema), *final["messages"], HumanMessage(extraer)],
            agente=nombre,
            modelo=contexto.modelo_de(rol),
            traza=contexto.traza,
            con_reserva=True,
        )
    except PresupuestoAgotado:
        lista = None
    propuestos = lista.hallazgos if lista else []
    hallazgos = [
        Hallazgo(id=f"{nombre}-{numero}", **propuesto.model_dump())
        for numero, propuesto in enumerate(propuestos, start=1)
    ]
    return hallazgos, final["corte"]
