"""Uso: python -m revisor <ruta-del-parche> [--sistema baseline]"""

import argparse

from .sistemas import SISTEMAS


def main() -> None:
    argumentos = argparse.ArgumentParser(description="Revisa un parche sobre el repositorio de prueba")
    argumentos.add_argument("parche")
    argumentos.add_argument("--sistema", choices=sorted(SISTEMAS), default="baseline")
    opciones = argumentos.parse_args()
    resultado = SISTEMAS[opciones.sistema]().run(opciones.parche)
    print(resultado["answer"])
    print(f"\nstatus: {resultado['status']} · modelo: {resultado['model']} · uso: {resultado['usage']}")
    print(f"traza: {resultado['trace']}")


if __name__ == "__main__":
    main()
