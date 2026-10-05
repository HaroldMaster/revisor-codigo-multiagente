"""Los frenos: límites en código que cortan a un agente que se descontrola.

- Tope de pasos por agente            (agentes/bucle.py)
- Presupuesto de tokens por corrida   (este módulo, comprobado antes de cada llamada)
- Detector de repetición              (agentes/bucle.py)
- Tiempo máximo de un check           (herramientas.py)

Al cortar, el agente entrega lo que tiene y el informe dice qué quedó sin hacer.
"""

from __future__ import annotations

import os

MAX_PASOS = int(os.getenv("REVISOR_MAX_PASOS", "12"))
LIMITE_TOKENS = int(os.getenv("REVISOR_LIMITE_TOKENS", "400000"))
# Parte del límite que solo pueden gastar los pasos de cierre: extraer los
# hallazgos y redactar el informe. Sin ella, una corrida que agota el
# presupuesto no entrega nada y pierde todo lo que gastó.
RESERVA_TOKENS = int(os.getenv("REVISOR_RESERVA_TOKENS", "30000"))
# La misma herramienta con los mismos argumentos más de K veces es un bucle.
K_REPETICION = 2


class PresupuestoAgotado(RuntimeError):
    pass
