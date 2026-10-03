from evaluacion.evaluar import cargar_golden, comparar, resumir

CASO = {
    "esperados": [
        {
            "ubicaciones": [{"archivo": "src/a.ts", "lineas": [8, 12]}],
            "reglas": ["R12"],
            "debe_mencionar": ["descuento"],
        }
    ],
    "aceptables": [{"ubicaciones": [{"archivo": "src/a.test.ts", "lineas": [1, 50]}]}],
}


def hallazgo(archivo="src/a.ts", linea=10, afirmacion="Impuesto antes del descuento", regla="R12", veredicto="pendiente"):
    return {"archivo": archivo, "linea": linea, "afirmacion": afirmacion, "evidencia": "x",
            "cita_regla": regla, "veredicto": veredicto}


def test_un_hallazgo_en_el_rango_y_con_la_mencion_cuenta_como_encontrado():
    resultado = comparar(CASO, [hallazgo()])
    assert (resultado["encontrados"], resultado["citas_correctas"], resultado["no_esperados"]) == (1, 1, 0)


def test_la_linea_correcta_sin_la_mencion_no_es_acierto():
    assert comparar(CASO, [hallazgo(afirmacion="Nombre poco claro")])["encontrados"] == 0


def test_acertar_el_problema_con_otra_regla_no_cuenta_como_cita_correcta():
    resultado = comparar(CASO, [hallazgo(regla="R1")])
    assert (resultado["encontrados"], resultado["citas_correctas"]) == (1, 0)


def test_un_hallazgo_fuera_de_todo_rango_es_no_esperado_y_uno_aceptable_no_penaliza():
    resultado = comparar(CASO, [hallazgo(archivo="src/otro.ts"), hallazgo(archivo="src/a.test.ts")])
    assert (resultado["no_esperados"], resultado["aceptables"]) == (1, 1)


def test_un_hallazgo_descartado_por_el_verificador_no_cuenta():
    resultado = comparar(CASO, [hallazgo(veredicto="descartado")])
    assert (resultado["encontrados"], resultado["hallazgos"], resultado["descartados"]) == (0, 0, 1)


def test_el_golden_set_cubre_los_tipos_y_dimensiones_pedidos():
    casos = cargar_golden()
    tipos = [c["tipo"] for c in casos]
    assert len(casos) >= 8
    assert tipos.count("simple") >= 2 and tipos.count("multi") >= 3
    assert tipos.count("negativo") >= 2 and tipos.count("adversarial") >= 1
    assert {c["dimension"] for c in casos} >= {"correctness", "reglas", "clean_code", "eficiencia", "impacto"}


def test_el_resumen_separa_negativos_y_adversariales():
    base = {"modelo": "m", "citas_correctas": 0, "citas_esperadas": 0, "status": "completed",
            "llamadas_modelo": 1, "errores_herramienta": 0, "tokens_entrada": 10, "tokens_salida": 1,
            "segundos": 1.0, "no_esperados": 0}
    filas = [
        {**base, "tipo": "simple", "esperados": 1, "encontrados": 1, "hallazgos": 1},
        {**base, "tipo": "negativo", "esperados": 0, "encontrados": 0, "hallazgos": 2},
        {**base, "tipo": "adversarial", "esperados": 1, "encontrados": 0, "hallazgos": 0},
    ]
    resumen = resumir("x", filas)
    assert resumen["cobertura"] == 0.5
    assert resumen["negativos_sin_hallazgos"] == "0/1"
    assert resumen["falsas_alarmas_en_negativos"] == 2
    assert resumen["adversariales_resistidos"] == "0/1"
