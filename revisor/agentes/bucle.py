"""El bucle de un agente, como grafo de LangGraph: modelo ↔ herramientas.

    inicio → modelo ──pidió herramientas y quedan pasos──→ herramientas ─┐
                ↑─────────────────────────────────────────────────────────┘
                └──respondió, o se alcanzó el tope de pasos──→ fin
"""

from __future__ import annotations

import json
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from ..contexto import Contexto
from ..herramientas import crear_herramientas
from ..llamada import invocar


class EstadoAgente(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    pasos: int
    corte: str | None


def ejecutar_agente(
    nombre: str,
    sistema: str,
    tarea: str,
    nombres_herramientas: list[str],
    contexto: Contexto,
    rol: str = "default",
) -> EstadoAgente:
    todas = crear_herramientas(
        contexto.perfil, contexto.indice, contexto.traza, nombre, contexto.citas_devueltas
    )
    herramientas = {n: todas[n] for n in nombres_herramientas}
    llm = contexto.llm_de(rol).bind_tools(list(herramientas.values()))
    modelo = contexto.modelo_de(rol)

    def nodo_modelo(estado: EstadoAgente) -> dict:
        respuesta = invocar(
            llm,
            [SystemMessage(sistema), *estado["messages"]],
            agente=nombre,
            modelo=modelo,
            traza=contexto.traza,
        )
        return {"messages": [respuesta], "pasos": estado["pasos"] + 1}

    def nodo_herramientas(estado: EstadoAgente) -> dict:
        observaciones = []
        for llamada in estado["messages"][-1].tool_calls:
            herramienta = herramientas.get(llamada["name"])
            if herramienta is None:
                contenido = json.dumps(
                    {"error": f"No existe la herramienta {llamada['name']}. Disponibles: {sorted(herramientas)}"},
                    ensure_ascii=False,
                )
            else:
                try:
                    contenido = herramienta.invoke(llamada["args"])
                except Exception as error:  # argumentos que no cumplen el esquema
                    contenido = json.dumps(
                        {"error": f"Argumentos inválidos para {llamada['name']}: {error}"},
                        ensure_ascii=False,
                    )
            observaciones.append(ToolMessage(content=contenido, tool_call_id=llamada["id"]))
        return {"messages": observaciones}

    def nodo_corte(estado: EstadoAgente) -> dict:
        # Cada llamada pendiente recibe su resultado: el historial queda coherente.
        pendientes = [
            ToolMessage(
                content=json.dumps({"error": "Tope de pasos alcanzado: no se ejecutó"}),
                tool_call_id=llamada["id"],
            )
            for llamada in estado["messages"][-1].tool_calls
        ]
        contexto.traza.evento("freno", freno="tope_de_pasos", agente=nombre, pasos=estado["pasos"])
        return {"messages": pendientes, "corte": "tope_de_pasos"}

    def siguiente(estado: EstadoAgente) -> str:
        if not estado["messages"][-1].tool_calls:
            return END
        return "herramientas" if estado["pasos"] < contexto.max_pasos else "corte"

    grafo = StateGraph(EstadoAgente)
    grafo.add_node("modelo", nodo_modelo)
    grafo.add_node("herramientas", nodo_herramientas)
    grafo.add_node("corte", nodo_corte)
    grafo.add_edge(START, "modelo")
    grafo.add_conditional_edges("modelo", siguiente, ["herramientas", "corte", END])
    grafo.add_edge("herramientas", "modelo")
    grafo.add_edge("corte", END)

    return grafo.compile().invoke(
        {"messages": [HumanMessage(tarea)], "pasos": 0, "corte": None},
        {"recursion_limit": 4 * contexto.max_pasos + 10},
    )
