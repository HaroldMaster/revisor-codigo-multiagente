import json
from pathlib import Path

import pytest

from evaluacion.guion import ModeloDeGuion, pide
from revisor.baseline import RevisorUnico
from revisor.frenos import PresupuestoAgotado
from revisor.traza import Traza

PARCHE = Path(__file__).resolve().parent.parent / "evaluacion" / "casos" / "C01.patch"
HALLAZGO = {
    "dimension": "reglas", "archivo": "src/pedidos/pedidos.ts", "linea": 24, "severidad": "alto",
    "afirmacion": "Impuesto antes del descuento.", "evidencia": "const impuestoCentavos = x;",
}


def correr(modelo, embeddings, tmp_path, **limites):
    resultado = RevisorUnico(
        llm_de=lambda rol: modelo, modelo_de=lambda rol: "guion", embeddings=embeddings,
        carpeta_trazas=tmp_path, **limites,
    ).run(str(PARCHE))
    eventos = [json.loads(l) for l in Path(resultado["trace"]).read_text(encoding="utf-8").splitlines()]
    return resultado, [e for e in eventos if e["tipo"] == "freno"], eventos


def test_el_trabajo_no_puede_gastar_la_reserva_y_el_cierre_si(tmp_path):
    traza = Traza(tmp_path, "p", limite_tokens=1000, reserva_tokens=300)
    traza.llamada("a", "m", 690, 20, 1)
    with pytest.raises(PresupuestoAgotado):
        traza.exigir_presupuesto()
    traza.exigir_presupuesto(con_reserva=True)
    traza.llamada("a", "m", 300, 0, 1)
    with pytest.raises(PresupuestoAgotado):
        traza.exigir_presupuesto(con_reserva=True)


def test_al_agotar_el_presupuesto_entrega_lo_que_tiene_y_lo_dice(embeddings, tmp_path):
    turnos = [pide("grep_repo", patron=f"t{n}") for n in range(20)]
    modelo = ModeloDeGuion(turnos, estructurados=[{"hallazgos": [HALLAZGO]}], tokens_por_turno=(30000, 0))
    resultado, frenos, eventos = correr(modelo, embeddings, tmp_path, limite_tokens=100000, reserva_tokens=35000, max_pasos=50)
    assert [f["freno"] for f in frenos] == ["presupuesto_de_tokens"]
    assert sum(e["tipo"] == "llamada" and e["agente"] == "reviewer_unico" for e in eventos) == 4
    assert resultado["status"] == "incompleto"
    assert len(resultado["hallazgos"]) == 1
    assert "presupuesto_de_tokens" in resultado["answer"]
    # El presupuesto se comprueba antes de cada llamada: no se conoce su costo de
    # antemano, así que el exceso posible es, como mucho, el de una llamada.
    assert resultado["usage"]["tokens_entrada"] <= 100000 + 30000


def test_la_misma_llamada_por_tercera_vez_corta_sin_ejecutarse(embeddings, tmp_path):
    modelo = ModeloDeGuion([pide("grep_repo", patron="x")], estructurados=[{"hallazgos": []}], repetir_ultimo=True)
    resultado, frenos, eventos = correr(modelo, embeddings, tmp_path, max_pasos=50)
    assert [f["freno"] for f in frenos] == ["repeticion"]
    assert sum(e["tipo"] == "herramienta" for e in eventos) == 2
    assert resultado["status"] == "incompleto"
    assert "repeticion" in resultado["answer"]


def test_el_tope_de_pasos_deja_aviso_y_no_una_respuesta_vacia(embeddings, tmp_path):
    turnos = [pide("grep_repo", patron=f"t{n}") for n in range(20)]
    modelo = ModeloDeGuion(turnos, estructurados=[{"hallazgos": [HALLAZGO]}])
    resultado, frenos, _ = correr(modelo, embeddings, tmp_path, max_pasos=3)
    assert [f["freno"] for f in frenos] == ["tope_de_pasos"]
    assert resultado["status"] == "incompleto"
    assert "tope_de_pasos" in resultado["answer"] and "src/pedidos/pedidos.ts:24" in resultado["answer"]


def test_tras_una_respuesta_vacia_se_reintenta_con_el_modelo_de_reintento(tmp_path):
    from langchain_core.messages import AIMessage

    from evaluacion.guion import responde
    from revisor.llamada import invocar

    traza = Traza(tmp_path, "p")
    se_queda_razonando = ModeloDeGuion([AIMessage(content="")])
    sin_razonar = ModeloDeGuion([responde("listo")])
    respuesta = invocar(se_queda_razonando, "hola", agente="a", modelo="m", traza=traza, llm_reintento=sin_razonar)
    assert respuesta.content == "listo"
    assert [e["error"] for e in traza.eventos] == ["respuesta vacía", None]


def test_una_llamada_que_falla_por_tiempo_tambien_se_reintenta(tmp_path):
    from evaluacion.guion import responde
    from revisor.llamada import invocar

    class SeCuelga:
        def invoke(self, mensajes):
            raise TimeoutError("60 s")

    traza = Traza(tmp_path, "p")
    respuesta = invocar(SeCuelga(), "hola", agente="a", modelo="m", traza=traza, llm_reintento=ModeloDeGuion([responde("listo")]))
    assert respuesta.content == "listo"
    assert "TimeoutError" in traza.eventos[0]["error"]


def test_si_el_reviewer_no_entrega_hallazgos_el_informe_lo_avisa(embeddings, tmp_path):
    from evaluacion.guion import responde

    modelo = ModeloDeGuion([responde("Revisé el cambio.")], estructurados=[])
    resultado, frenos, _ = correr(modelo, embeddings, tmp_path)
    assert [f["freno"] for f in frenos] == ["respuesta_vacia_al_extraer"]
    assert resultado["status"] == "incompleto"
    assert "respuesta_vacia_al_extraer" in resultado["answer"]
