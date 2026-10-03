"""0.a — El revisor que no mira.

Un modelo recibe un diff y nada más: ni herramientas ni las reglas del repo.
Se le pide un review con citas. Después, el código comprueba cada cita
contra el repositorio real. Se corre con dos niveles de razonamiento, porque
fallan distinto y ninguno da error: con poco, no ve el bug; con mucho, lo ve
y se inventa las reglas y los archivos que cita.

Uso: python -m evaluacion.parte0.a_revisor_sin_herramientas
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from evaluacion.repo_temporal import repo_con_parches
from revisor.config import get_llm, id_modelo
from revisor.llamada import invocar_estructurado
from revisor.traza import Traza

AQUI = Path(__file__).resolve().parent
PARCHE = AQUI / "a_impuesto.patch"


class Cita(BaseModel):
    archivo: str = Field(description="Ruta del archivo con el problema")
    linea: int = Field(description="Número de línea en ese archivo")
    evidencia: str = Field(description="Copia literal de esa línea")
    regla_id: str = Field(description="Identificador de la regla del repositorio que se incumple")
    texto_regla: str = Field(description="Cita literal del texto de esa regla en el repositorio")
    otros_archivos_afectados: list[str] = Field(
        description="Rutas de otros archivos del repositorio que se ven afectados"
    )


class Review(BaseModel):
    hallazgos: list[Cita]


PROMPT = """Eres el revisor de código de este repositorio de TypeScript. Revisa el diff y
entrega tus hallazgos. Para cada uno indica archivo, línea, la línea literal, el
identificador y el texto literal de la regla del repositorio que incumple, y qué otros
archivos del repositorio quedan afectados.

Diff:
{diff}"""


def main() -> None:
    for esfuerzo in ("low", "high"):
        print(f"================ razonamiento: {esfuerzo}")
        os.environ["LLM_REASONING_EFFORT"] = esfuerzo
        revisar()
        print()


def revisar() -> None:
    diff = PARCHE.read_text(encoding="utf-8")
    traza = Traza(tempfile.mkdtemp(), "parte0a")
    modelo = id_modelo()
    review = invocar_estructurado(
        get_llm(), Review, PROMPT.format(diff=diff), agente="revisor_ingenuo", modelo=modelo, traza=traza
    )
    if review is None:
        print("el modelo no devolvió un review; ver la traza")
        return
    print(f"modelo: {modelo}")
    print(f"hallazgos devueltos: {len(review.hallazgos)}\n")

    comprobadas = falsas = 0
    with repo_con_parches(PARCHE) as repo:
        reglas = (repo / "CLAUDE.md").read_text(encoding="utf-8")
        for numero, cita in enumerate(review.hallazgos, start=1):
            print(f"--- hallazgo {numero}: {cita.archivo}:{cita.linea}  regla {cita.regla_id!r}")
            print(f"    evidencia:   {cita.evidencia.strip()[:100]}")
            print(f"    texto regla: {cita.texto_regla.strip()[:100]}")
            archivo = repo / cita.archivo
            lineas = archivo.read_text(encoding="utf-8").splitlines() if archivo.is_file() else []
            en_linea = (
                0 < cita.linea <= len(lineas)
                and cita.evidencia.strip() == lineas[cita.linea - 1].strip()
            )
            comprobaciones = {
                "el archivo existe": archivo.is_file(),
                "la línea citada contiene esa evidencia": en_linea,
                "la regla existe con ese id": f"### {cita.regla_id}." in reglas,
                "el texto de la regla es literal": cita.texto_regla.strip() in reglas,
            }
            for otro in cita.otros_archivos_afectados:
                comprobaciones[f"existe el archivo afectado {otro}"] = (repo / otro).is_file()
            for nombre, pasa in comprobaciones.items():
                comprobadas += 1
                falsas += not pasa
                print(f"    [{'ok' if pasa else 'FALSO'}] {nombre}")
    print(f"\ncitas comprobadas: {comprobadas} · falsas: {falsas}")
    print("excepciones: 0 · el modelo respondió con normalidad y el formato era válido")
    print(f"tokens: {traza.uso()}")
    traza.cerrar("completed")


if __name__ == "__main__":
    main()
