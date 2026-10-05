"""Toda llamada al modelo pasa por aquí: mide, registra en la traza y
reintenta cuando el modelo devuelve una respuesta vacía."""

from __future__ import annotations

import time

from .traza import Traza


def texto_de(mensaje) -> str:
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    return "".join(b.get("text", "") for b in contenido if isinstance(b, dict))


def invocar(
    llm, mensajes, *, agente: str, modelo: str, traza: Traza, reintentos_vacia: int = 1,
    con_reserva: bool = False,
):
    respuesta = None
    traza.exigir_presupuesto(con_reserva)
    for _ in range(reintentos_vacia + 1):
        inicio = time.perf_counter()
        try:
            respuesta = llm.invoke(mensajes)
        except Exception as error:
            latencia = round((time.perf_counter() - inicio) * 1000)
            traza.llamada(agente, modelo, 0, 0, latencia, error=f"{type(error).__name__}: {error}")
            raise
        latencia = round((time.perf_counter() - inicio) * 1000)
        uso = respuesta.usage_metadata or {}
        vacia = not texto_de(respuesta).strip() and not respuesta.tool_calls
        traza.llamada(
            agente,
            modelo,
            uso.get("input_tokens", 0),
            uso.get("output_tokens", 0),
            latencia,
            error="respuesta vacía" if vacia else None,
        )
        if not vacia:
            break
    return respuesta


def invocar_estructurado(
    llm, esquema, mensajes, *, agente: str, modelo: str, traza: Traza, reintentos: int = 1,
    con_reserva: bool = False,
):
    """Como invocar, para una respuesta con esquema fijo. Devuelve el objeto
    validado, o None si tras los reintentos el modelo no lo entregó."""
    from .config import estructurado

    traza.exigir_presupuesto(con_reserva)
    ejecutable = estructurado(llm, esquema)
    for _ in range(reintentos + 1):
        inicio = time.perf_counter()
        try:
            resultado = ejecutable.invoke(mensajes)
        except Exception as error:
            latencia = round((time.perf_counter() - inicio) * 1000)
            traza.llamada(agente, modelo, 0, 0, latencia, error=f"{type(error).__name__}: {error}")
            raise
        latencia = round((time.perf_counter() - inicio) * 1000)
        uso = resultado["raw"].usage_metadata or {}
        objeto = resultado["parsed"]
        motivo = None
        if objeto is None:
            fin = resultado["raw"].response_metadata.get("finish_reason")
            motivo = f"sin salida estructurada (finish_reason={fin}): {resultado['parsing_error']}"
        traza.llamada(
            agente, modelo, uso.get("input_tokens", 0), uso.get("output_tokens", 0), latencia,
            error=motivo,
        )
        if objeto is not None:
            return objeto
    return None
