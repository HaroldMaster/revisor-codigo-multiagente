"""0.c — Los tests en verde que no prueban nada.

Un cambio añade una función con un bug de borde y un test que solo comprueba
que la función existe. Lint, tipos y tests pasan: quien mire el código de
salida lo aprueba. Dos comprobaciones de código lo rechazan sin ningún modelo.

Uso: python -m evaluacion.parte0.c_tests_en_verde
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from evaluacion.repo_temporal import repo_con_parches
from revisor.herramientas import crear_herramientas
from revisor.perfil import cargar_perfil

AQUI = Path(__file__).resolve().parent
CAMBIO = AQUI / "c_volumen.patch"
MUTANTE = AQUI / "c_mutante.patch"
AFIRMACIONES_DEBILES = ("toBeDefined", "not.toThrow", "toBeTruthy", "not.toBeNull")


def correr(repo: Path, tipo: str) -> int:
    herramientas = crear_herramientas(cargar_perfil(repo), indice=None)
    return json.loads(herramientas["correr_checks"].invoke({"tipo": tipo}))["codigo_salida"]


def afirmaciones_del_test_nuevo(parche: Path) -> list[str]:
    agregadas = [
        linea[1:]
        for linea in parche.read_text(encoding="utf-8").splitlines()
        if linea.startswith("+") and not linea.startswith("+++")
    ]
    return re.findall(r"expect\(.*?\)\.([\w.]+)\(", "\n".join(agregadas))


def main() -> None:
    print("1) El revisor ingenuo: mira el código de salida")
    with repo_con_parches(CAMBIO) as repo:
        codigos = {tipo: correr(repo, tipo) for tipo in ("lint", "tipos", "tests")}
    for tipo, codigo in codigos.items():
        print(f"    {tipo:<6} código de salida {codigo}")
    print(f"    veredicto ingenuo: {'APROBADO' if not any(codigos.values()) else 'RECHAZADO'}\n")

    print("2) Comprobación estática: qué afirma el test que llegó con el cambio")
    afirmaciones = afirmaciones_del_test_nuevo(CAMBIO)
    debiles = [a for a in afirmaciones if a in AFIRMACIONES_DEBILES]
    print(f"    afirmaciones nuevas: {afirmaciones}")
    print(f"    que no comprueban ningún valor: {len(debiles)} de {len(afirmaciones)}")
    print(f"    veredicto: {'RECHAZADO' if len(debiles) == len(afirmaciones) else 'aprobado'}\n")

    print("3) Comprobación por mutación: se rompe la función a propósito y se corren los tests")
    with repo_con_parches(CAMBIO, MUTANTE) as repo:
        codigo = correr(repo, "tests")
    print(f"    tests con la función devolviendo un valor absurdo: código de salida {codigo}")
    print(f"    veredicto: {'RECHAZADO, los tests no detectan el cambio' if codigo == 0 else 'aprobado'}")


if __name__ == "__main__":
    main()
