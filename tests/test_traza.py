import json

from revisor.traza import Traza


def test_cada_evento_queda_en_disco_sin_esperar_al_cierre(tmp_path):
    traza = Traza(tmp_path, "prueba")
    traza.llamada("reviewer", "modelo-x", 100, 20, 350)
    lineas = traza.ruta.read_text(encoding="utf-8").splitlines()
    assert json.loads(lineas[0])["tokens_entrada"] == 100


def test_suma_el_uso_total_y_por_agente(tmp_path):
    traza = Traza(tmp_path, "prueba")
    traza.llamada("reviewer", "m", 100, 20, 10)
    traza.llamada("reviewer", "m", 300, 30, 10)
    traza.llamada("verificador", "m", 50, 5, 10, error="respuesta vacía")
    traza.herramienta("reviewer", "grep_repo", {"patron": "x"}, 12, 3)
    traza.cerrar("completed")

    assert traza.uso() == {"tokens_entrada": 450, "tokens_salida": 55}
    assert traza.uso_por_agente()["reviewer"] == {
        "llamadas": 2,
        "tokens_entrada": 400,
        "tokens_salida": 50,
    }
    cierre = json.loads(traza.ruta.read_text(encoding="utf-8").splitlines()[-1])
    assert cierre["status"] == "completed"
    assert cierre["uso"]["tokens_entrada"] == 450
