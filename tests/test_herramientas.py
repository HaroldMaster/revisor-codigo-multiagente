import json

import pytest

from revisor import herramientas as modulo
from revisor.herramientas import crear_herramientas
from revisor.rag.indice import construir_indice
from revisor.traza import Traza


@pytest.fixture()
def caja(perfil, embeddings, tmp_path):
    indice = construir_indice(perfil, embeddings, con_docs=False, cache=False)
    traza = Traza(tmp_path, "prueba")
    citas: set[str] = set()
    herramientas = crear_herramientas(perfil, indice, traza, "reviewer", citas)
    return herramientas, traza, citas


def test_leer_archivo_numera_las_lineas(caja):
    herramientas, _, _ = caja
    salida = herramientas["leer_archivo"].invoke({"ruta": "src/errores.ts", "desde": 1, "hasta": 2})
    assert salida.splitlines()[1] == "1: export class ErrorDominio extends Error {"


def test_leer_archivo_no_sale_del_repo(caja):
    herramientas, _, _ = caja
    salida = herramientas["leer_archivo"].invoke({"ruta": "../requirements.txt"})
    assert "sale del repositorio" in json.loads(salida)["error"]


def test_leer_archivo_no_entrega_mas_del_tope_aunque_se_pida(caja, monkeypatch):
    herramientas, _, _ = caja
    monkeypatch.setattr(modulo, "MAX_LINEAS", 5)
    salida = herramientas["leer_archivo"].invoke(
        {"ruta": "src/inventario/inventario.ts", "desde": 1, "hasta": 10000}
    )
    assert "líneas 1-5 de" in salida
    assert "pide desde=6" in salida


def test_un_archivo_inexistente_es_un_error_devuelto_y_queda_en_la_traza(caja):
    herramientas, traza, _ = caja
    salida = herramientas["leer_archivo"].invoke({"ruta": "src/nada.ts"})
    assert "error" in json.loads(salida)
    assert traza.eventos[-1]["error"] is not None


def test_grep_encuentra_los_usos_fuera_del_archivo_que_define(caja):
    herramientas, _, _ = caja
    salida = herramientas["grep_repo"].invoke({"patron": "porcentajeDe"})
    assert "src/utils/dinero.ts" in salida
    assert "src/pedidos/pedidos.ts" in salida
    assert "src/descuentos/descuentos.ts" in salida


def test_grep_sin_resultados_lo_dice(caja):
    herramientas, _, _ = caja
    assert "Sin coincidencias" in herramientas["grep_repo"].invoke({"patron": "noExisteEsto"})


def test_grep_acepta_un_patron_que_no_es_regex_valida(caja):
    herramientas, _, _ = caja
    assert "coincidencias" in herramientas["grep_repo"].invoke({"patron": "crearPedido("})


def test_buscar_reglas_devuelve_ids_y_los_anota_como_citas_validas(caja):
    herramientas, _, citas = caja
    salida = json.loads(
        herramientas["buscar_reglas"].invoke({"pregunta": "impuesto después del descuento"})
    )
    assert len(salida) == modulo.K_FRAGMENTOS
    assert {f["id"] for f in salida} == citas
    assert "R12" in citas


def test_correr_checks_ejecuta_el_comando_del_perfil(caja):
    herramientas, _, _ = caja
    salida = json.loads(herramientas["correr_checks"].invoke({"tipo": "tipos"}))
    assert salida["codigo_salida"] == 0


def test_correr_checks_no_pasa_las_variables_del_entorno(caja, monkeypatch, perfil):
    herramientas, _, _ = caja
    monkeypatch.setenv("CLAVE_SECRETA", "no-debe-llegar")
    monkeypatch.setitem(perfil.checks, "lint", "env")
    salida = json.loads(herramientas["correr_checks"].invoke({"tipo": "lint"}))
    assert "CLAVE_SECRETA" not in salida["salida"]


def test_correr_checks_corta_al_superar_el_tiempo(caja, monkeypatch, perfil):
    herramientas, _, _ = caja
    monkeypatch.setattr(modulo, "TIEMPO_CHECK_S", 1)
    monkeypatch.setitem(perfil.checks, "lint", "sleep 30")
    salida = json.loads(herramientas["correr_checks"].invoke({"tipo": "lint"}))
    assert "superó" in salida["error"]


def test_correr_checks_rechaza_un_tipo_fuera_de_la_lista(caja):
    herramientas, _, _ = caja
    with pytest.raises(Exception):
        herramientas["correr_checks"].invoke({"tipo": "rm -rf ."})
