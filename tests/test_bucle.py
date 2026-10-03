import json

import pytest
from langchain_core.messages import ToolMessage

from evaluacion.guion import ModeloDeGuion, pide, responde
from revisor.agentes.bucle import ejecutar_agente
from revisor.agentes.prompts import TODAS
from revisor.contexto import Contexto
from revisor.rag.indice import construir_indice
from revisor.traza import Traza


@pytest.fixture()
def contexto_con(perfil, embeddings, tmp_path):
    def crear(modelo, max_pasos=12):
        indice = construir_indice(perfil, embeddings, con_docs=False, cache=False)
        return Contexto(
            perfil, indice, Traza(tmp_path, "prueba"),
            llm_de=lambda rol: modelo, modelo_de=lambda rol: "guion", max_pasos=max_pasos,
        )

    return crear


def observaciones(estado):
    return [m for m in estado["messages"] if isinstance(m, ToolMessage)]


def test_el_resultado_de_la_herramienta_vuelve_al_modelo(contexto_con):
    modelo = ModeloDeGuion([pide("grep_repo", patron="porcentajeDe"), responde("listo")])
    estado = ejecutar_agente("a", "sistema", "tarea", TODAS, contexto_con(modelo))
    assert "src/utils/dinero.ts" in observaciones(estado)[0].content
    assert estado["messages"][-1].content == "listo"
    assert estado["pasos"] == 2
    assert estado["corte"] is None


def test_una_herramienta_que_no_existe_es_una_observacion_de_error(contexto_con):
    modelo = ModeloDeGuion([pide("leer_datos", ruta="x"), responde("listo")])
    estado = ejecutar_agente("a", "sistema", "tarea", TODAS, contexto_con(modelo))
    assert "No existe la herramienta leer_datos" in json.loads(observaciones(estado)[0].content)["error"]
    assert estado["messages"][-1].content == "listo"


def test_argumentos_que_no_cumplen_el_esquema_no_matan_la_corrida(contexto_con):
    modelo = ModeloDeGuion([pide("correr_checks", tipo="rm -rf ."), responde("listo")])
    estado = ejecutar_agente("a", "sistema", "tarea", TODAS, contexto_con(modelo))
    assert "Argumentos inválidos" in json.loads(observaciones(estado)[0].content)["error"]
    assert estado["messages"][-1].content == "listo"


def test_un_agente_solo_puede_usar_las_herramientas_que_se_le_dan(contexto_con):
    modelo = ModeloDeGuion([pide("correr_checks", tipo="lint"), responde("listo")])
    estado = ejecutar_agente("a", "sistema", "tarea", ["leer_archivo"], contexto_con(modelo))
    assert "No existe la herramienta correr_checks" in observaciones(estado)[0].content


def test_el_tope_de_pasos_corta_y_deja_el_historial_coherente(contexto_con):
    modelo = ModeloDeGuion([pide("grep_repo", patron="x")], repetir_ultimo=True)
    contexto = contexto_con(modelo, max_pasos=3)
    estado = ejecutar_agente("a", "sistema", "tarea", TODAS, contexto)
    assert estado["corte"] == "tope_de_pasos"
    assert estado["pasos"] == 3
    pedidas = [l["id"] for m in estado["messages"] for l in getattr(m, "tool_calls", [])]
    respondidas = [m.tool_call_id for m in observaciones(estado)]
    assert pedidas == respondidas
    assert any(e["tipo"] == "freno" for e in contexto.traza.eventos)
