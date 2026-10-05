"""Lee los resultados crudos y los resume para el informe. Ninguna cifra del
informe se escribe a mano: todas salen de resultados/ a través de este módulo."""

from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "resultados"

SISTEMAS = [
    ("baseline", "Baseline: un agente"),
    ("baseline_con_pistas", "Un agente con las instrucciones de los reviewers"),
    ("baseline_razonamiento_medio", "Un agente, razonamiento medio"),
    ("baseline_razonamiento_alto", "Un agente, razonamiento alto"),
    ("multiagente", "Multiagente (7 agentes)"),
    ("sin_verificador", "Multiagente sin verificador"),
    ("sin_rag", "Multiagente sin RAG"),
    ("multiagente_razonamiento_alto", "Multiagente, razonamiento alto"),
]


def leer_csv(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    with ruta.open(encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def filas_por_caso(conjunto: str = "") -> dict[str, dict[int, list[dict]]]:
    """sistema → repetición → filas de resultados_<sistema>[_grande][_rN].csv"""
    datos: dict[str, dict[int, list[dict]]] = defaultdict(dict)
    marca = f"_{conjunto}" if conjunto else ""
    for sistema, _ in SISTEMAS:
        for repeticion in range(1, 10):
            sufijo = "" if repeticion == 1 else f"_r{repeticion}"
            filas = leer_csv(RESULTADOS / f"resultados_{sistema}{marca}{sufijo}.csv")
            if filas:
                datos[sistema][repeticion] = filas
    return datos


def _numero(valor: str) -> float:
    return float(valor) if valor not in ("", None) else 0.0


def resumen_por_sistema(conjunto: str = "") -> dict[str, dict]:
    """Por sistema: la lista de valores de cada métrica, uno por repetición."""
    resumen = {}
    for sistema, repeticiones in filas_por_caso(conjunto).items():
        metricas = defaultdict(list)
        for filas in repeticiones.values():
            negativos = [f for f in filas if f["tipo"] == "negativo"]
            adversariales = [f for f in filas if f["tipo"] == "adversarial"]
            metricas["encontrados"].append(sum(_numero(f["encontrados"]) for f in filas))
            metricas["esperados"].append(sum(_numero(f["esperados"]) for f in filas))
            metricas["citas_correctas"].append(sum(_numero(f["citas_correctas"]) for f in filas))
            metricas["citas_esperadas"].append(sum(_numero(f["citas_esperadas"]) for f in filas))
            metricas["falsas_alarmas"].append(sum(_numero(f["hallazgos"]) for f in negativos))
            metricas["adversarial"].append(
                sum(f["encontrados"] == f["esperados"] for f in adversariales)
            )
            metricas["no_esperados"].append(sum(_numero(f["no_esperados"]) for f in filas))
            metricas["sin_reportar"].append(
                sum(1 for f in filas if _numero(f["esperados"]) > 0 and _numero(f["hallazgos"]) == 0)
            )
            metricas["hallazgos"].append(sum(_numero(f["hallazgos"]) for f in filas))
            metricas["incompletas"].append(sum(f["status"] != "completed" for f in filas))
            metricas["llamadas"].append(sum(_numero(f["llamadas_modelo"]) for f in filas))
            metricas["errores_herramienta"].append(sum(_numero(f["errores_herramienta"]) for f in filas))
            metricas["frenos"].append(sum(_numero(f.get("frenos", 0)) for f in filas))
            metricas["tokens_entrada"].append(sum(_numero(f["tokens_entrada"]) for f in filas))
            metricas["tokens_salida"].append(sum(_numero(f["tokens_salida"]) for f in filas))
            metricas["segundos"].append(sum(_numero(f["segundos"]) for f in filas))
        resumen[sistema] = dict(metricas, repeticiones=len(repeticiones), modelo=filas[0]["modelo"])
    return resumen


def media(valores: list[float]) -> float:
    return statistics.mean(valores) if valores else 0.0


def dec(valor: float, decimales: int = 1) -> str:
    """Número con punto decimal, para que no se confunda con las comas del texto."""
    return f"{valor:.{decimales}f}"


def media_y_rango(valores: list[float], decimales: int = 1) -> str:
    if not valores:
        return "—"
    minimo, maximo = min(valores), max(valores)
    if minimo == maximo:
        return f"{minimo:.0f}"
    return f"{dec(media(valores), decimales)} ({minimo:.0f}–{maximo:.0f})"


def miles(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", " ")


def aciertos_por_caso(conjunto: str = "") -> dict[str, dict[str, str]]:
    """caso → sistema → «encontrados/esperados» sumados sobre las repeticiones."""
    tabla: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for sistema, repeticiones in filas_por_caso(conjunto).items():
        for filas in repeticiones.values():
            for f in filas:
                celda = tabla[f["caso"]][sistema]
                celda[0] += int(f["encontrados"])
                celda[1] += int(f["esperados"])
                celda[2] += int(f["hallazgos"])
    return tabla


def eventos(ruta: Path) -> list[dict]:
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def calibracion() -> dict:
    """Lo que usaron de verdad las corridas medidas: para contrastar los límites."""
    pasos, tokens, checks, frenos = defaultdict(list), defaultdict(list), [], Counter()
    for carpeta in sorted((RESULTADOS / "trazas").iterdir()):
        if "_grande" in carpeta.name:
            continue
        sistema = carpeta.name.rsplit("_r", 1)[0] if carpeta.name[-3:-1] == "_r" else carpeta.name
        for traza in carpeta.glob("*.jsonl"):
            ev = eventos(traza)
            llamadas = Counter(e["agente"] for e in ev if e["tipo"] == "llamada")
            reviewers = [n for agente, n in llamadas.items() if agente.startswith("reviewer")]
            pasos[sistema].append(max(reviewers or [0]))
            tokens[sistema].append(
                sum(e["tokens_entrada"] + e["tokens_salida"] for e in ev if e["tipo"] == "llamada")
            )
            checks += [e["latencia_ms"] for e in ev if e["tipo"] == "herramienta" and e["nombre"] == "correr_checks"]
            for e in ev:
                if e["tipo"] == "freno":
                    frenos[(sistema, e["freno"], e.get("agente", ""))] += 1
    return {"pasos": pasos, "tokens": tokens, "checks": sorted(checks), "frenos": frenos}


def uso_por_agente(sistema: str) -> dict[str, dict[str, float]]:
    """Tokens por agente, promedio por repetición, sumando los casos."""
    total: dict[str, Counter] = defaultdict(Counter)
    repeticiones = 0
    for carpeta in (RESULTADOS / "trazas").iterdir():
        nombre = carpeta.name
        if nombre != sistema and not (nombre.startswith(sistema + "_r") and nombre[len(sistema) + 2:].isdigit()):
            continue
        repeticiones += 1
        for traza in carpeta.glob("*.jsonl"):
            for e in eventos(traza):
                if e["tipo"] == "llamada":
                    total[e["agente"]]["llamadas"] += 1
                    total[e["agente"]]["tokens_entrada"] += e["tokens_entrada"]
                    total[e["agente"]]["tokens_salida"] += e["tokens_salida"]
    return {a: {k: v / max(repeticiones, 1) for k, v in c.items()} for a, c in total.items()}


def _carpetas(prefijo: str) -> list[Path]:
    """Las carpetas de trazas de un sistema y conjunto: <prefijo>, <prefijo>_r2, <prefijo>_r3."""
    return [c for c in (RESULTADOS / "trazas" / f"{prefijo}{r}" for r in ("", "_r2", "_r3")) if c.exists()]


def llamadas_vacias(prefijo: str) -> dict:
    """Llamadas al modelo que no devolvieron nada, y el tiempo que consumieron."""
    llamadas = [e for c in _carpetas(prefijo) for t in c.glob("*.jsonl") for e in eventos(t) if e["tipo"] == "llamada"]
    vacias = [e for e in llamadas if e["error"]]
    return {
        "llamadas": len(llamadas),
        "vacias": len(vacias),
        "seg_vacias": sum(e["latencia_ms"] for e in vacias) / 1000,
        "seg_modelo": sum(e["latencia_ms"] for e in llamadas) / 1000,
        "mas_lenta": max((e["latencia_ms"] for e in llamadas), default=0) / 1000,
    }


def segundos_por_caso(sistema: str, conjunto: str = "", etiqueta: str = "") -> dict[str, list[float]]:
    marca = (f"_{conjunto}" if conjunto else "") + (f"_{etiqueta}" if etiqueta else "")
    tiempos: dict[str, list[float]] = defaultdict(list)
    for r in ("", "_r2", "_r3"):
        for f in leer_csv(RESULTADOS / f"resultados_{sistema}{marca}{r}.csv"):
            tiempos[f["caso"]].append(float(f["segundos"]))
    return tiempos


def encontrados_con_etiqueta(sistema: str, conjunto: str, etiqueta: str) -> list[int]:
    marca = f"_{conjunto}" + (f"_{etiqueta}" if etiqueta else "")
    return [
        sum(int(f["encontrados"]) for f in filas)
        for r in ("", "_r2", "_r3")
        if (filas := leer_csv(RESULTADOS / f"resultados_{sistema}{marca}{r}.csv"))
    ]


def bugs_del_caso_complejo(sistemas: list[str]) -> dict[str, list[int]]:
    """Por sistema, en cuántas de las corridas encontró cada uno de los tres bugs de G03."""
    golden = json.loads((RAIZ / "evaluacion" / "golden_set_grande.json").read_text(encoding="utf-8"))
    esperados = next(c for c in golden if c["id"] == "G03")["esperados"]

    def lo_encuentra(hallazgos: list[dict], esperado: dict) -> bool:
        for h in hallazgos:
            en_rango = any(
                h["archivo"] == u["archivo"] and u["lineas"][0] <= h["linea"] <= u["lineas"][1]
                for u in esperado["ubicaciones"]
            )
            texto = f"{h['afirmacion']} {h['evidencia']}".lower()
            if en_rango and any(p.lower() in texto for p in esperado["debe_mencionar"]):
                return True
        return False

    tabla = {}
    for sistema in sistemas:
        cuenta = [0, 0, 0, 0]
        for carpeta in _carpetas(f"{sistema}_grande"):
            traza = carpeta / "G03.jsonl"
            if not traza.exists():
                continue
            cuenta[3] += 1
            hallazgos = [h for e in eventos(traza) if e["tipo"] == "resultado" for h in e["hallazgos"] if h["veredicto"] != "descartado"]
            for i, esperado in enumerate(esperados):
                cuenta[i] += lo_encuentra(hallazgos, esperado)
        tabla[sistema] = cuenta
    return tabla


def informes_del_sintetizador(sistema: str = "multiagente") -> dict:
    """En cuántas corridas redactó el sintetizador, y cuántas veces el código le rechazó
    el informe por mencionar algo que no estaba en los hallazgos."""
    redactadas = con_rechazo = por_codigo = 0
    for carpeta in _carpetas(sistema):
        for traza in carpeta.glob("*.jsonl"):
            ev = eventos(traza)
            redactadas += any(e["tipo"] == "llamada" and e["agente"] == "sintetizador" for e in ev)
            rechazos = [e for e in ev if e["tipo"] == "procedencia"]
            con_rechazo += bool(rechazos)
            por_codigo += any("generado por código" in str(e) for e in rechazos)
    return {"redactadas": redactadas, "con_rechazo": con_rechazo, "por_codigo": por_codigo}
