"""Corre un sistema contra el golden set y escribe los resultados crudos.

    python -m evaluacion.evaluar --verificar            # comprueba la verdad de cada caso
    python -m evaluacion.evaluar --sistema baseline     # mide un sistema

Salida, en resultados/:
    resultados_<sistema>.csv   una fila por caso
    resumen.csv                una fila por sistema
    trazas/<sistema>/<caso>.jsonl
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from evaluacion.repo_temporal import repo_con_parches
from revisor.perfil import cargar_perfil

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
RESULTADOS = RAIZ / "resultados"
GOLDEN = AQUI / "golden_set.json"
CHECKS = ("lint", "tipos", "tests")


def cargar_golden(solo: list[str] | None = None) -> list[dict]:
    casos = json.loads(GOLDEN.read_text(encoding="utf-8"))
    return [c for c in casos if not solo or c["id"] in solo]


# ------------------------------------------------------------ la verdad, ejecutable

def _correr(repo: Path, comando: str) -> int:
    entorno = {"PATH": os.environ.get("PATH", ""), "HOME": os.environ.get("HOME", ""), "CI": "1"}
    return subprocess.run(
        shlex.split(comando), cwd=repo, env=entorno, capture_output=True, timeout=180
    ).returncode


def _test_oculto(repo: Path, caso_id: str) -> int:
    destino = repo / "src" / "__ocultos__"
    destino.mkdir(exist_ok=True)
    shutil.copy(AQUI / "casos" / "ocultos" / f"{caso_id}.test.ts", destino / f"{caso_id}.test.ts")
    perfil = cargar_perfil(repo)
    return _correr(repo, f"{perfil.checks['tests']} src/__ocultos__")


def verificar_caso(caso: dict) -> dict:
    """Demuestra en código que el problema del caso existe (o que el caso está limpio)."""
    verdad = caso["verdad"]
    parche = AQUI / caso["parche"]
    with repo_con_parches(parche) as repo:
        perfil = cargar_perfil(repo)
        checks = {tipo: _correr(repo, perfil.checks[tipo]) for tipo in CHECKS}
        if verdad["tipo"] == "check_falla":
            demostrado = checks[verdad["check"]] != 0
            detalle = f"el check {verdad['check']} falla con el parche"
        elif verdad["tipo"] == "test_oculto":
            demostrado = _test_oculto(repo, caso["id"]) != 0
            detalle = "el test oculto falla con el parche"
            if verdad["pasa_en_base"]:
                with repo_con_parches() as base:
                    demostrado = demostrado and _test_oculto(base, caso["id"]) == 0
                detalle += " y pasa sin él"
        elif verdad["tipo"] == "patron":
            texto = (repo / verdad["archivo"]).read_text(encoding="utf-8")
            demostrado = re.search(verdad["patron"], texto, flags=re.DOTALL) is not None
            detalle = "el patrón está en el archivo modificado"
        elif verdad["tipo"] == "simbolo_sin_uso":
            apariciones = sum(
                archivo.read_text(encoding="utf-8").count(verdad["simbolo"])
                for archivo in perfil.archivos_de_codigo()
            )
            demostrado = apariciones == 1
            detalle = f"{verdad['simbolo']} aparece {apariciones} vez en todo el código"
        else:  # limpio
            demostrado = not any(checks.values())
            detalle = "lint, tipos y tests pasan"
    silencioso = not any(checks.values())
    return {"caso": caso["id"], "demostrado": demostrado, "detalle": detalle, "checks_en_verde": silencioso}


# ------------------------------------------------------------ comparar con lo esperado

def _en(hallazgo: dict, entrada: dict) -> bool:
    return any(
        hallazgo["archivo"] == u["archivo"] and u["lineas"][0] <= hallazgo["linea"] <= u["lineas"][1]
        for u in entrada["ubicaciones"]
    )


def _menciona(hallazgo: dict, palabras: list[str]) -> bool:
    texto = f"{hallazgo['afirmacion']} {hallazgo['evidencia']}".lower()
    return any(palabra.lower() in texto for palabra in palabras)


def comparar(caso: dict, hallazgos: list[dict]) -> dict:
    vigentes = [h for h in hallazgos if h.get("veredicto") != "descartado"]
    encontrados = citas_esperadas = citas_correctas = 0
    for esperado in caso["esperados"]:
        coincidentes = [
            h for h in vigentes
            if _en(h, esperado)
            and ("debe_mencionar" not in esperado or _menciona(h, esperado["debe_mencionar"]))
        ]
        encontrados += bool(coincidentes)
        if "reglas" in esperado:
            citas_esperadas += 1
            citas_correctas += any(h.get("cita_regla") in esperado["reglas"] for h in coincidentes)
    en_esperados = [h for h in vigentes if any(_en(h, e) for e in caso["esperados"])]
    en_aceptables = [
        h for h in vigentes if h not in en_esperados and any(_en(h, e) for e in caso["aceptables"])
    ]
    return {
        "esperados": len(caso["esperados"]),
        "encontrados": encontrados,
        "citas_esperadas": citas_esperadas,
        "citas_correctas": citas_correctas,
        "hallazgos": len(vigentes),
        "aceptables": len(en_aceptables),
        "no_esperados": len(vigentes) - len(en_esperados) - len(en_aceptables),
        "descartados": len(hallazgos) - len(vigentes),
    }


# ------------------------------------------------------------ correr y escribir

def medir_caso(sistema: str, caso: dict) -> dict:
    from revisor.sistemas import SISTEMAS

    carpeta = Path(tempfile.mkdtemp(prefix="trazas-"))
    inicio = time.perf_counter()
    resultado = SISTEMAS[sistema](carpeta_trazas=carpeta).run(str(AQUI / caso["parche"]))
    segundos = round(time.perf_counter() - inicio, 1)
    destino = RESULTADOS / "trazas" / sistema / f"{caso['id']}.jsonl"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(resultado["trace"], destino)
    shutil.rmtree(carpeta, ignore_errors=True)
    eventos = [json.loads(linea) for linea in destino.read_text(encoding="utf-8").splitlines()]
    usos = [e for e in eventos if e["tipo"] == "herramienta"]
    return {
        "sistema": sistema,
        "caso": caso["id"],
        "tipo": caso["tipo"],
        "dimension": caso["dimension"],
        **comparar(caso, resultado["hallazgos"]),
        "status": resultado["status"],
        "llamadas_modelo": sum(e["tipo"] == "llamada" for e in eventos),
        "usos_herramienta": len(usos),
        "errores_herramienta": sum(e["error"] is not None for e in usos),
        "frenos": sum(e["tipo"] == "freno" for e in eventos),
        "tokens_entrada": resultado["usage"]["tokens_entrada"],
        "tokens_salida": resultado["usage"]["tokens_salida"],
        "segundos": segundos,
        "modelo": resultado["model"],
        "traza": destino.relative_to(RAIZ).as_posix(),
    }


def resumir(sistema: str, filas: list[dict]) -> dict:
    positivos = [f for f in filas if f["tipo"] in ("simple", "multi")]
    negativos = [f for f in filas if f["tipo"] == "negativo"]
    adversariales = [f for f in filas if f["tipo"] == "adversarial"]
    esperados = sum(f["esperados"] for f in filas)
    encontrados = sum(f["encontrados"] for f in filas)
    return {
        "sistema": sistema,
        "modelo": filas[0]["modelo"],
        "casos": len(filas),
        "esperados": esperados,
        "encontrados": encontrados,
        "cobertura": round(encontrados / esperados, 3) if esperados else "",
        "casos_positivos_completos": f"{sum(f['encontrados'] == f['esperados'] for f in positivos)}/{len(positivos)}",
        "negativos_sin_hallazgos": f"{sum(f['hallazgos'] == 0 for f in negativos)}/{len(negativos)}",
        "falsas_alarmas_en_negativos": sum(f["hallazgos"] for f in negativos),
        "adversariales_resistidos": f"{sum(f['encontrados'] == f['esperados'] for f in adversariales)}/{len(adversariales)}",
        "no_esperados": sum(f["no_esperados"] for f in filas),
        "citas_correctas": f"{sum(f['citas_correctas'] for f in filas)}/{sum(f['citas_esperadas'] for f in filas)}",
        "corridas_no_completadas": sum(f["status"] != "completed" for f in filas),
        "llamadas_modelo": sum(f["llamadas_modelo"] for f in filas),
        "errores_herramienta": sum(f["errores_herramienta"] for f in filas),
        "tokens_entrada": sum(f["tokens_entrada"] for f in filas),
        "tokens_salida": sum(f["tokens_salida"] for f in filas),
        "segundos": round(sum(f["segundos"] for f in filas), 1),
    }


def escribir_csv(ruta: Path, filas: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def actualizar_resumen(fila: dict) -> None:
    ruta = RESULTADOS / "resumen.csv"
    anteriores = []
    if ruta.exists():
        with ruta.open(encoding="utf-8") as archivo:
            anteriores = [f for f in csv.DictReader(archivo) if f["sistema"] != fila["sistema"]]
    escribir_csv(ruta, [*anteriores, fila])


def main() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    argumentos.add_argument("--sistema", default="baseline")
    argumentos.add_argument("--solo", nargs="*", help="ids de casos, por ejemplo C01 N01")
    argumentos.add_argument("--verificar", action="store_true", help="solo comprueba la verdad de los casos")
    argumentos.add_argument("--paralelo", type=int, default=4)
    opciones = argumentos.parse_args()
    casos = cargar_golden(opciones.solo)

    if opciones.verificar:
        with ThreadPoolExecutor(opciones.paralelo) as hilos:
            verificaciones = list(hilos.map(verificar_caso, casos))
        for v in verificaciones:
            marca = "ok   " if v["demostrado"] else "FALLA"
            silencio = "checks en verde" if v["checks_en_verde"] else "algún check falla"
            print(f"{marca} {v['caso']}  {v['detalle']}  ({silencio})")
        escribir_csv(RESULTADOS / "verificacion_golden_set.csv", verificaciones)
        raise SystemExit(0 if all(v["demostrado"] for v in verificaciones) else 1)

    with ThreadPoolExecutor(opciones.paralelo) as hilos:
        filas = list(hilos.map(lambda caso: medir_caso(opciones.sistema, caso), casos))
    for f in filas:
        print(
            f"{f['caso']} {f['tipo']:<11} encontrados {f['encontrados']}/{f['esperados']} · "
            f"hallazgos {f['hallazgos']} (no esperados {f['no_esperados']}) · {f['status']} · "
            f"{f['tokens_entrada']} tok · {f['segundos']} s"
        )
    if not opciones.solo:
        escribir_csv(RESULTADOS / f"resultados_{opciones.sistema}.csv", filas)
        resumen = resumir(opciones.sistema, filas)
        actualizar_resumen(resumen)
        print()
        for clave, valor in resumen.items():
            print(f"{clave:<28} {valor}")


if __name__ == "__main__":
    main()
