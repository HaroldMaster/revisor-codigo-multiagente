import json
from pathlib import Path

from evaluacion.guion import ModeloDeGuion, pide, responde
from revisor.baseline import RevisorUnico, archivos_del_diff

PARCHE = Path(__file__).resolve().parent.parent / "evaluacion" / "parte0" / "a_impuesto.patch"
HALLAZGO = {
    "dimension": "reglas",
    "archivo": "src/pedidos/pedidos.ts",
    "linea": 24,
    "severidad": "alto",
    "afirmacion": "El impuesto se calcula antes del descuento.",
    "evidencia": "const impuestoCentavos = Math.round(subtotalCentavos * 0.15);",
    "cita_regla": "R12",
}


def revisor(modelo, embeddings, tmp_path):
    return RevisorUnico(
        llm_de=lambda rol: modelo, modelo_de=lambda rol: "guion",
        embeddings=embeddings, carpeta_trazas=tmp_path,
    )


def test_extrae_los_archivos_del_diff():
    assert archivos_del_diff(PARCHE.read_text(encoding="utf-8")) == ["src/pedidos/pedidos.ts"]


def test_run_cumple_el_contrato_y_revisa_la_copia_con_el_parche(embeddings, tmp_path):
    modelo = ModeloDeGuion(
        [pide("grep_repo", patron="0\\.15"), responde("Encontré un problema.")],
        estructurados=[{"hallazgos": [HALLAZGO]}],
    )
    resultado = revisor(modelo, embeddings, tmp_path).run(str(PARCHE))

    assert set(resultado) >= {"answer", "trace", "status", "model", "usage"}
    assert resultado["status"] == "completed"
    assert resultado["model"] == "guion"
    assert resultado["usage"] == {"tokens_entrada": 300, "tokens_salida": 30}
    assert resultado["hallazgos"][0]["cita_regla"] == "R12"
    assert "src/pedidos/pedidos.ts:24" in resultado["answer"]

    eventos = [json.loads(l) for l in Path(resultado["trace"]).read_text(encoding="utf-8").splitlines()]
    grep = next(e for e in eventos if e["tipo"] == "herramienta")
    assert grep["tamano_resultado"] > len("Sin coincidencias para '0\\\\.15'")
    assert eventos[-1]["tipo"] == "cierre"

    # La traza guarda qué pidió el modelo, qué observó y qué respondió.
    pidio = next(e for e in eventos if e["tipo"] == "llamada" and e["pide"])
    assert pidio["pide"] == [{"nombre": "grep_repo", "argumentos": {"patron": "0\\.15"}}]
    assert "coincidencias" in grep["resultado"] or "Sin coincidencias" in grep["resultado"]
    respondio = next(e for e in eventos if e["tipo"] == "llamada" and e["respuesta"])
    assert respondio["respuesta"] == "Encontré un problema."
    final = next(e for e in eventos if e["tipo"] == "resultado")
    assert final["hallazgos"][0]["cita_regla"] == "R12"


def test_un_fallo_deja_traza_y_status_failed(embeddings, tmp_path):
    modelo = ModeloDeGuion([])  # sin turnos: la primera llamada al modelo falla
    resultado = revisor(modelo, embeddings, tmp_path).run(str(PARCHE))
    assert resultado["status"] == "failed"
    cierre = json.loads(Path(resultado["trace"]).read_text(encoding="utf-8").splitlines()[-1])
    assert cierre["status"] == "failed"
    assert "IndexError" in cierre["error"]


def test_sin_salida_estructurada_no_inventa_hallazgos(embeddings, tmp_path):
    modelo = ModeloDeGuion([responde("Todo bien.")], estructurados=[])
    resultado = revisor(modelo, embeddings, tmp_path).run(str(PARCHE))
    assert resultado["hallazgos"] == []
    assert "Sin hallazgos" in resultado["answer"]
