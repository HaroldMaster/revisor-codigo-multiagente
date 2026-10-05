"""Genera informe/informe.html e informe/informe.pdf a partir de los resultados crudos.

Uso: python informe/generar_informe.py
"""

from __future__ import annotations

import html
import json
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(AQUI))

import datos  # noqa: E402
import textos  # noqa: E402
from revisor.perfil import cargar_perfil  # noqa: E402
from revisor.rag.indice import recolectar  # noqa: E402

CSS = """
body { font-family: 'Liberation Serif', 'Times New Roman', serif; font-size: 11pt; line-height: 1.45; color: #222; max-width: 760px; margin: 40px auto; }
h1 { font-size: 20pt; margin-bottom: 4px; }
.sub { color: #555; font-size: 10pt; margin-bottom: 30px; }
h2 { font-size: 14pt; border-bottom: 1px solid #999; padding-bottom: 3px; margin-top: 34px; }
h3 { font-size: 11.5pt; margin-top: 22px; }
pre { background: #f2f2f2; border: 1px solid #ddd; padding: 8px 10px; font-size: 8pt; white-space: pre-wrap; word-break: break-word; }
code { background: #f2f2f2; font-size: 9pt; padding: 0 2px; }
table { border-collapse: collapse; font-size: 8.5pt; margin: 8px 0; }
th, td { border: 1px solid #bbb; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background: #eee; }
td.n, th.n { text-align: right; white-space: nowrap; }
.nota { color: #555; font-size: 9pt; }
blockquote { margin: 8px 0; padding-left: 10px; border-left: 3px solid #bbb; }
h2, h3 { break-after: avoid; }
table, pre { break-inside: avoid; }
"""

partes: list[str] = []
p = partes.append


def tabla(encabezado, filas, numericas=()):
    th = "".join(f"<th class='{'n' if i in numericas else ''}'>{h}</th>" for i, h in enumerate(encabezado))
    tr = "".join(
        "<tr>" + "".join(f"<td class='{'n' if i in numericas else ''}'>{c}</td>" for i, c in enumerate(f)) + "</tr>"
        for f in filas
    )
    return f"<table><tr>{th}</tr>{tr}</table>"


def pre(texto: str) -> str:
    return "<pre>" + html.escape(texto.rstrip("\n")) + "</pre>"


def archivo(ruta: str, desde: str | None = None, hasta: str | None = None, quitar: tuple = ()) -> str:
    lineas = (RAIZ / ruta).read_text(encoding="utf-8").splitlines()
    if desde:
        lineas = lineas[next(i for i, l in enumerate(lineas) if desde in l):]
    if hasta:
        lineas = lineas[: next(i for i, l in enumerate(lineas) if hasta in l)]
    return pre("\n".join(l for l in lineas if not any(q in l for q in quitar)))


def pasos_de(traza: str, maximo: int = 14, ancho: int = 150, solo: tuple = (), errores: bool = False) -> str:
    """Una traza en limpio: qué pidió cada agente, qué observó y qué respondió."""
    lineas = []
    agente_actual = ""
    for e in datos.eventos(RAIZ / traza):
        agente_actual = e.get("agente", agente_actual) if e["tipo"] in ("llamada", "herramienta") else agente_actual
        if solo and e["tipo"] in ("llamada", "herramienta") and not any(agente_actual.startswith(a) for a in solo):
            continue
        if len(lineas) >= maximo:
            lineas.append("…")
            break
        if e["tipo"] == "llamada":
            if errores and e.get("error"):
                motivo = " ".join(e["error"].split())[:70]
                lineas.append(f"{e['agente']} FALLA  {motivo} · {e['tokens_salida']} tokens de salida · {e['latencia_ms'] / 1000:.0f} s")
            elif e.get("pide"):
                for llamada in e["pide"]:
                    argumentos = json.dumps(llamada["argumentos"], ensure_ascii=False)
                    lineas.append(f"{e['agente']} pide   {llamada['nombre']}({argumentos})"[:ancho])
            elif e.get("respuesta"):
                lineas.append(f"{e['agente']} dice   {' '.join(e['respuesta'].split())}"[:ancho])
        elif e["tipo"] == "herramienta":
            lineas.append(f"    observa  {' '.join((e.get('resultado') or '').split())}"[:ancho])
        elif e["tipo"] in ("freno", "veredicto", "unir", "comprobar_en_codigo", "procedencia"):
            detalle = {k: v for k, v in e.items() if k not in ("tipo", "t_ms")}
            lineas.append(f"  [{e['tipo']}] {json.dumps(detalle, ensure_ascii=False)}"[:ancho])
        elif e["tipo"] == "cierre":
            lineas.append(f"  [cierre] status={e['status']} tokens={e['uso']}")
    return pre("\n".join(lineas))


for seccion in textos.SECCIONES:
    seccion(p, tabla=tabla, pre=pre, archivo=archivo, pasos_de=pasos_de, datos=datos, RAIZ=RAIZ,
            recolectar=recolectar, cargar_perfil=cargar_perfil, tomllib=tomllib, Counter=Counter)

documento = (
    "<!doctype html><html lang='es'><head><meta charset='utf-8'><title>informe</title>"
    f"<style>{CSS}</style></head><body>" + "\n".join(partes) + "</body></html>"
)
(AQUI / "informe.html").write_text(documento, encoding="utf-8")
subprocess.run(
    ["google-chrome", "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
     f"--print-to-pdf={AQUI / 'informe.pdf'}", str(AQUI / "informe.html")],
    check=True, capture_output=True,
)
print(f"informe: {AQUI / 'informe.pdf'}")
