"""Parte 3 — Los frenos, probados haciéndolos saltar.

Cada escenario usa un modelo de guion que se porta mal a propósito, así que
no gasta nada: el freno es código nuestro. Deja una traza por freno en
resultados/frenos/.

Uso: python -m evaluacion.forzar_frenos
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import tempfile
from pathlib import Path

from evaluacion.guion import ModeloDeGuion, pide, responde
from evaluacion.repo_temporal import REPO_PRUEBA
from revisor import herramientas as modulo_herramientas
from revisor.agentes.bucle import ejecutar_agente
from revisor.baseline import RevisorUnico
from revisor.contexto import Contexto
from revisor.perfil import cargar_perfil
from revisor.traza import Traza

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI.parent / "resultados" / "frenos"
PARCHE = AQUI / "casos" / "C01.patch"
HALLAZGO = {
    "dimension": "reglas",
    "archivo": "src/pedidos/pedidos.ts",
    "linea": 24,
    "severidad": "alto",
    "afirmacion": "El impuesto se calcula antes de restar el descuento.",
    "evidencia": "const impuestoCentavos = porcentajeDe(subtotalCentavos, IMPUESTO_PORCENTAJE);",
    "cita_regla": None,
}


class SinEmbeddings:
    """El índice no se consulta en estos escenarios: vectores fijos, sin red."""

    model = "ninguno"

    def embed_documents(self, textos):
        return [[1.0, 0.0] for _ in textos]

    def embed_query(self, texto):
        return [1.0, 0.0]


def correr_revisor(nombre: str, modelo: ModeloDeGuion, **limites) -> dict:
    carpeta = Path(tempfile.mkdtemp())
    resultado = RevisorUnico(
        llm_de=lambda rol: modelo, modelo_de=lambda rol: "guion", embeddings=SinEmbeddings(),
        carpeta_trazas=carpeta, **limites,
    ).run(str(PARCHE))
    destino = SALIDA / f"{nombre}.jsonl"
    shutil.copy(resultado["trace"], destino)
    return {**resultado, "trace": destino}


def mostrar(titulo: str, traza: Path, respuesta: str, status: str) -> None:
    eventos = [json.loads(linea) for linea in traza.read_text(encoding="utf-8").splitlines()]
    frenos = [e for e in eventos if e["tipo"] == "freno"]
    print(f"=== {titulo}")
    print(f"    llamadas al modelo: {sum(e['tipo'] == 'llamada' for e in eventos)} · "
          f"usos de herramienta: {sum(e['tipo'] == 'herramienta' for e in eventos)} · status: {status}")
    for freno in frenos:
        detalle = {k: v for k, v in freno.items() if k not in ("tipo", "t_ms")}
        print(f"    FRENO: {json.dumps(detalle, ensure_ascii=False)}")
    print(f"    saltó el freno: {'sí' if frenos or 'superó' in respuesta else 'NO'}")
    print("    respuesta entregada:")
    for linea in respuesta.splitlines():
        print(f"      {linea}")
    print(f"    traza: {traza.relative_to(AQUI.parent)}\n")


def tope_de_pasos() -> None:
    # El modelo nunca termina: en cada turno pide una búsqueda distinta.
    turnos = [pide("grep_repo", patron=f"termino{n}") for n in range(30)]
    modelo = ModeloDeGuion(turnos, estructurados=[{"hallazgos": [HALLAZGO]}])
    r = correr_revisor("tope_de_pasos", modelo, max_pasos=4)
    mostrar("Tope de pasos (límite 4)", r["trace"], r["answer"], r["status"])


def presupuesto_de_tokens() -> None:
    # Cada turno cuesta 30 000 tokens de entrada: el historial se reenvía entero.
    turnos = [pide("leer_archivo", ruta="src/pedidos/pedidos.ts", desde=n, hasta=n + 5) for n in range(1, 30)]
    modelo = ModeloDeGuion(turnos, estructurados=[{"hallazgos": [HALLAZGO]}], tokens_por_turno=(30000, 500))
    r = correr_revisor("presupuesto_de_tokens", modelo, limite_tokens=120000, reserva_tokens=35000, max_pasos=50)
    mostrar("Presupuesto de tokens (120 000, con 35 000 de reserva para el cierre)", r["trace"], r["answer"], r["status"])


def repeticion() -> None:
    # El modelo se atasca pidiendo siempre lo mismo.
    modelo = ModeloDeGuion(
        [pide("grep_repo", patron="porcentajeDe")], estructurados=[{"hallazgos": []}], repetir_ultimo=True
    )
    r = correr_revisor("repeticion", modelo, max_pasos=50)
    mostrar("Detector de repetición (la misma llamada más de 2 veces)", r["trace"], r["answer"], r["status"])


def tiempo_maximo() -> None:
    # Un check que se cuelga: se mata al grupo de procesos y el agente sigue.
    perfil = cargar_perfil(REPO_PRUEBA)
    perfil = dataclasses.replace(perfil, checks={**perfil.checks, "tests": "sleep 60"})
    traza = Traza(SALIDA, "tiempo_maximo")
    traza.ruta.unlink(missing_ok=True)
    modelo = ModeloDeGuion([pide("correr_checks", tipo="tests"), responde("Los tests no terminaron; no pude confirmarlo.")])
    contexto = Contexto(perfil, None, traza, llm_de=lambda rol: modelo, modelo_de=lambda rol: "guion")
    original = modulo_herramientas.TIEMPO_CHECK_S
    modulo_herramientas.TIEMPO_CHECK_S = 2
    try:
        final = ejecutar_agente("reviewer", "sistema", "tarea", ["correr_checks"], contexto)
    finally:
        modulo_herramientas.TIEMPO_CHECK_S = original
    traza.cerrar("completed")
    destino = SALIDA / "tiempo_maximo.jsonl"
    traza.ruta.replace(destino)
    observacion = final["messages"][-2].content
    mostrar("Tiempo máximo de un check (límite 2 s, el comando duerme 60 s)", destino,
            f"observación que recibió el modelo: {observacion}\n{final['messages'][-1].content}", "completed")


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    tope_de_pasos()
    presupuesto_de_tokens()
    repeticion()
    tiempo_maximo()


if __name__ == "__main__":
    main()
