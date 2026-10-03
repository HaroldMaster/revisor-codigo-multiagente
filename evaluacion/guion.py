"""Modelo de guion: devuelve lo que se le escribió, en orden, sin llamar a nadie.

Sirve para probar el bucle y forzar los frenos sin gastar: el freno es código
nuestro y no depende de lo que decida un modelo real.
"""

from __future__ import annotations

from itertools import count

from langchain_core.messages import AIMessage

_ids = count(1)


def pide(nombre: str, **argumentos) -> AIMessage:
    """Un turno del modelo que pide una herramienta."""
    return AIMessage(
        content="",
        tool_calls=[{"name": nombre, "args": argumentos, "id": f"guion-{next(_ids)}"}],
    )


def responde(texto: str) -> AIMessage:
    """Un turno del modelo que da su respuesta final."""
    return AIMessage(content=texto)


class ModeloDeGuion:
    def __init__(self, turnos: list[AIMessage], estructurados: list | None = None,
                 tokens_por_turno: tuple[int, int] = (100, 10), repetir_ultimo: bool = False):
        self._turnos = list(turnos)
        self._estructurados = list(estructurados or [])
        self._tokens = tokens_por_turno
        self._repetir_ultimo = repetir_ultimo
        self.mensajes_recibidos: list[list] = []

    def _uso(self) -> dict:
        entrada, salida = self._tokens
        return {"input_tokens": entrada, "output_tokens": salida, "total_tokens": entrada + salida}

    def bind_tools(self, herramientas):
        return self

    def invoke(self, mensajes):
        self.mensajes_recibidos.append(list(mensajes))
        if self._repetir_ultimo and len(self._turnos) == 1:
            plantilla = self._turnos[0]
            turno = AIMessage(
                content=plantilla.content,
                tool_calls=[{**llamada, "id": f"guion-{next(_ids)}"} for llamada in plantilla.tool_calls],
            )
        else:
            turno = self._turnos.pop(0)
        turno.usage_metadata = self._uso()
        return turno

    def with_structured_output(self, esquema, **_):
        guion = self

        class Estructurado:
            def invoke(self, mensajes):
                guion.mensajes_recibidos.append(list(mensajes))
                crudo = AIMessage(content="", usage_metadata=guion._uso())
                datos = guion._estructurados.pop(0) if guion._estructurados else None
                if datos is None:
                    crudo.response_metadata = {"finish_reason": "length"}
                    return {"raw": crudo, "parsed": None, "parsing_error": None}
                return {"raw": crudo, "parsed": esquema.model_validate(datos), "parsing_error": None}

        return Estructurado()
