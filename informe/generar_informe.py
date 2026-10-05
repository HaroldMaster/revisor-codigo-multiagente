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
figure { margin: 14px 0; text-align: center; }
figure img { max-width: 100%; }
figcaption { font-size: 9pt; color: #444; margin-top: 4px; }
.traza table { font-size: 7.5pt; width: 100%; }
.traza td:nth-child(1) { white-space: nowrap; }
.traza td:nth-child(2) { width: 34%; }
.entrega { border: 1px solid #999; padding: 6px 12px; margin: 10px 0; font-size: 9.5pt; break-inside: avoid; }
.entrega .rotulo { font-size: 8.5pt; color: #555; border-bottom: 1px solid #ccc; padding-bottom: 3px; margin-bottom: 4px; }
.entrega p { margin: 5px 0; } .entrega ul { margin: 4px 0; padding-left: 18px; }
h2, h3 { break-after: avoid; }
pre, figure, table { break-inside: avoid; }
.traza table { break-inside: auto; }
.traza tr { break-inside: avoid; }
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


def archivo(ruta: str, desde: str | None = None, hasta: str | None = None, quitar: tuple = (), saltar: tuple = ()) -> str:
    """El contenido de un archivo de salida. `saltar=(a, b)` omite desde la línea que
    contiene a hasta la que contiene b, sin incluir esta última."""
    lineas = (RAIZ / ruta).read_text(encoding="utf-8").splitlines()
    if desde:
        lineas = lineas[next(i for i, l in enumerate(lineas) if desde in l):]
    if hasta:
        lineas = lineas[: next(i for i, l in enumerate(lineas) if hasta in l)]
    if saltar:
        inicio = next(i for i, l in enumerate(lineas) if saltar[0] in l)
        fin = next(i for i, l in enumerate(lineas) if i > inicio and saltar[1] in l)
        lineas = lineas[:inicio] + ["(...)"] + lineas[fin:]
    return pre("\n".join(l for l in lineas if not any(q in l for q in quitar)))


ANCHO_FIGURA = {"bucle": 72, "baseline": 62}


def diagrama(nombre: str, pie: str) -> str:
    """Un diagrama hecho en Mermaid (informe/diagramas/<nombre>.mmd), como imagen."""
    return (
        f"<figure><img src='diagramas/{nombre}.png' alt='{pie}' style='max-width: {ANCHO_FIGURA.get(nombre, 100)}%'>"
        f"<figcaption>{pie}</figcaption></figure>"
    )


NOMBRES = {"reviewer_unico": "reviewer único", "reviewer_bugs": "reviewer de bugs", "reviewer_reglas": "reviewer de reglas",
           "reviewer_clean_code": "reviewer de clean code", "reviewer_eficiencia": "reviewer de eficiencia",
           "reviewer_impacto": "reviewer de impacto", "verificador": "verificador", "sintetizador": "sintetizador"}


def pasos_de(traza: str, maximo: int = 14, ancho: int = 170, solo: tuple = (), errores: bool = False,
             desde_el_final: bool = False) -> str:
    """Una traza como tabla. Cada fila es una acción completa de un agente: la
    herramienta que pidió junto con lo que recibió, o lo que respondió."""
    filas = []
    pendientes: dict[tuple, list] = {}  # (agente, herramienta) -> filas que esperan su resultado

    def corto(texto) -> str:
        texto = " ".join(str(texto).split())
        return html.escape(texto[:ancho] + ("…" if len(texto) > ancho else ""))

    def respuesta_legible(texto: str) -> str:
        try:
            datos_json = json.loads(texto)
        except (ValueError, TypeError):
            return corto(texto.replace("**", "").replace("`", ""))
        if isinstance(datos_json, dict) and "hallazgos" in datos_json:
            hallazgos = datos_json["hallazgos"]
            if not hallazgos:
                return "Entrega la ficha sin ningún hallazgo."
            primero = hallazgos[0]
            return corto(f"Entrega {len(hallazgos)} hallazgo(s) en la ficha. El primero: {primero['archivo']}:{primero['linea']}, {primero['afirmacion']}")
        if isinstance(datos_json, dict) and "veredicto" in datos_json:
            return corto(f"Veredicto: {datos_json['veredicto']}. {datos_json.get('motivo', '')}")
        return corto(texto)

    for e in datos.eventos(RAIZ / traza):
        agente = e.get("agente", "")
        if e["tipo"] in ("llamada", "herramienta") and solo and not any(agente.startswith(a) for a in solo):
            continue
        quien = NOMBRES.get(agente, agente)
        if e["tipo"] == "llamada":
            if errores and e.get("error"):
                filas.append([quien, "ninguna, la llamada falla", corto(f"La llamada al modelo falla: {e['error']} ({e['tokens_salida']} tokens de salida, {e['latencia_ms'] / 1000:.0f} s)")])
            elif e.get("pide"):
                for llamada in e["pide"]:
                    argumentos = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in llamada["argumentos"].items())
                    fila = [quien, f"<code>{corto(llamada['nombre'] + '(' + argumentos + ')')}</code>", "(sin resultado en la traza)"]
                    filas.append(fila)
                    pendientes.setdefault((agente, llamada["nombre"]), []).append(fila)
            elif e.get("respuesta"):
                filas.append([quien, "ninguna, da su respuesta", respuesta_legible(e["respuesta"])])
        elif e["tipo"] == "herramienta":
            cola = pendientes.get((agente, e["nombre"]))
            if cola:
                cola.pop(0)[2] = "Recibe: " + corto(e.get("resultado") or "")
        elif e["tipo"] in ("freno", "veredicto", "unir", "comprobar_en_codigo", "procedencia"):
            detalle = {k: v for k, v in e.items() if k not in ("tipo", "t_ms")}
            filas.append(["código del sistema", e["tipo"].replace("_", " "), corto(json.dumps(detalle, ensure_ascii=False))])
        elif e["tipo"] == "cierre":
            filas.append(["código del sistema", "cierre", f"La corrida termina con estado {e['status']} y {e['uso']['tokens_entrada']} tokens de entrada."])
    if len(filas) > maximo and desde_el_final:
        filas = [["…", "…", "Pasos anteriores de la traza."]] + filas[-maximo:]
    elif len(filas) > maximo:
        filas = filas[:maximo] + [["…", "…", "La traza continúa."]]
    return "<div class='traza'>" + tabla(["quién", "qué herramienta pide", "qué recibe o qué responde"], filas) + "</div>"


def informe_de(traza: str, titulo: str) -> str:
    """El informe de review que entregó una corrida, tal como quedó guardado en su traza."""
    import re

    texto = next(e["informe"] for e in datos.eventos(RAIZ / traza) if e["tipo"] == "resultado")

    def en_linea(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", t)

    partes, en_lista = [], False
    for linea in texto.splitlines():
        if linea.startswith("- "):
            partes.append(("" if en_lista else "<ul>") + f"<li>{en_linea(linea[2:])}")
            en_lista = True
        elif linea.startswith("  ") and en_lista:
            partes.append(f"<br>{en_linea(linea.strip())}")
        else:
            if en_lista:
                partes.append("</li></ul>")
                en_lista = False
            if linea.startswith("#"):
                partes.append(f"<p><b>{en_linea(linea.lstrip('# '))}</b></p>")
            elif linea.strip():
                partes.append(f"<p>{en_linea(linea)}</p>")
    if en_lista:
        partes.append("</li></ul>")
    return f"<div class='entrega'><div class='rotulo'>{titulo}</div>{''.join(partes)}</div>"


for seccion in textos.SECCIONES:
    seccion(p, tabla=tabla, pre=pre, archivo=archivo, pasos_de=pasos_de, diagrama=diagrama, informe_de=informe_de, datos=datos, RAIZ=RAIZ,
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
