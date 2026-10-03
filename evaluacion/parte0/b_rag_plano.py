"""0.b — El RAG plano que no trae la regla.

Índice TF-IDF sobre las reglas del repo, sin ningún modelo. Se consulta con el
código del diff, que es lo que haría un revisor descuidado, y la regla que
aplica no aparece: el código y la regla no comparten palabras. Después se
consulta con la intención del cambio, y aparece.

Uso: python -m evaluacion.parte0.b_rag_plano
"""

from __future__ import annotations

import math
import re
from collections import Counter

from evaluacion.repo_temporal import REPO_PRUEBA
from revisor.perfil import cargar_perfil
from revisor.rag.indice import recolectar

LINEA_DEL_DIFF = "const impuestoCentavos = Math.round(subtotalCentavos * 0.15);"
INTENCION = "en qué orden se calculan el impuesto y el descuento, y con qué porcentaje"
REGLAS_QUE_APLICAN = {"R12", "R14"}
K = 3


def palabras(texto: str) -> list[str]:
    return re.findall(r"[a-záéíóúñ]+|\d+(?:\.\d+)?", texto.lower())


def tfidf(documentos: list[list[str]]) -> tuple[list[dict[str, float]], dict[str, float]]:
    total = len(documentos)
    frecuencia_documental = Counter(p for d in documentos for p in set(d))
    idf = {p: math.log(total / n) + 1 for p, n in frecuencia_documental.items()}
    return [{p: c * idf[p] for p, c in Counter(d).items()} for d in documentos], idf


def coseno(a: dict[str, float], b: dict[str, float]) -> float:
    producto = sum(valor * b.get(p, 0) for p, valor in a.items())
    norma = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return producto / norma if norma else 0.0


def main() -> None:
    fragmentos = recolectar(cargar_perfil(REPO_PRUEBA), con_docs=False)
    vectores, idf = tfidf([palabras(f.texto) for f in fragmentos])
    print(f"fragmentos indexados: {len(fragmentos)} (solo reglas del repo, TF-IDF, sin modelo)")
    print(f"reglas que aplican al cambio: {sorted(REGLAS_QUE_APLICAN)}\n")
    for etiqueta, consulta in (("el código del diff", LINEA_DEL_DIFF), ("la intención", INTENCION)):
        vector = {p: c * idf.get(p, 0) for p, c in Counter(palabras(consulta)).items()}
        orden = sorted(
            ((coseno(vector, v), f.id) for v, f in zip(vectores, fragmentos)), reverse=True
        )[:K]
        recuperadas = {identificador for _, identificador in orden}
        print(f"consulta con {etiqueta}: {consulta!r}")
        for similitud, identificador in orden:
            print(f"    {identificador:<10} similitud {similitud:.3f}")
        print(f"    reglas correctas recuperadas: {len(recuperadas & REGLAS_QUE_APLICAN)} de {len(REGLAS_QUE_APLICAN)}\n")


if __name__ == "__main__":
    main()
