"""Informe en Markdown a partir de las fichas de hallazgo."""

from __future__ import annotations

from .estado import Hallazgo

ORDEN = {"critico": 0, "alto": 1, "medio": 2}


def redactar(hallazgos: list[Hallazgo], avisos: list[str] | None = None) -> str:
    lineas = ["## Informe de review", ""]
    for aviso in avisos or []:
        lineas += [f"> {aviso}", ""]
    if not hallazgos:
        lineas.append("Sin hallazgos.")
        return "\n".join(lineas)
    for hallazgo in sorted(hallazgos, key=lambda h: (ORDEN[h.severidad], h.archivo, h.linea)):
        regla = f" · regla {hallazgo.cita_regla}" if hallazgo.cita_regla else ""
        lineas += [
            f"- **[{hallazgo.severidad}] {hallazgo.archivo}:{hallazgo.linea}** "
            f"({hallazgo.dimension}{regla}, {hallazgo.veredicto})",
            f"  {hallazgo.afirmacion}",
            f"  `{hallazgo.evidencia.strip()}`",
        ]
    return "\n".join(lineas)
