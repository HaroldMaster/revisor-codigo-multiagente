# Revisor de código multiagente

Sistema en LangGraph que recibe un diff de un repositorio y devuelve un informe de review con hallazgos verificados. Taller 03 de MMIA 6013 IA Generativa y Agentes (USFQ), opción de tema libre.

## Carpetas

- `repo-prueba/`: el repositorio que se revisa. Mini tienda en TypeScript con sus reglas (`CLAUDE.md`) y su perfil (`perfil.toml`).
- `revisor/`: el sistema. Configuración del modelo, estado, herramientas, RAG y traza.
- `evaluacion/`: la Parte 0, el modelo de guion y la copia temporal del repo.
- `tests/`: pruebas del sistema; no llaman a ningún modelo.

## Preparación

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
(cd repo-prueba && npm ci)
cp .env.example .env          # y completar
.venv/bin/python -m revisor.rag.ingesta   # descarga las fuentes aprobadas del RAG
```

Con la H200 de la USFQ hace falta la VPN GlobalProtect conectada. El id del modelo no se escribe: se lee de `/v1/models`.

## Uso

```bash
.venv/bin/python -m revisor evaluacion/parte0/a_impuesto.patch --sistema multiagente
```

Recibe la ruta de un parche, lo aplica sobre una copia temporal de `repo-prueba/` y devuelve el informe. La traza de la corrida queda en `corridas/`.

Desde código, el contrato es `RevisorUnico().run(ruta_del_parche)`, que devuelve `answer`, `trace`, `status`, `model` y `usage`.

## Parte 0

```bash
.venv/bin/python -m evaluacion.parte0.a_revisor_sin_herramientas
.venv/bin/python -m evaluacion.parte0.b_rag_plano
.venv/bin/python -m evaluacion.parte0.c_tests_en_verde
```

La salida cruda de cada uno está en `evaluacion/parte0/salidas/`.

## Golden set y medición

```bash
.venv/bin/python -m evaluacion.construir_casos        # regenera los parches y golden_set.json
.venv/bin/python -m evaluacion.evaluar --verificar    # demuestra en código la verdad de cada caso
.venv/bin/python -m evaluacion.evaluar --sistema baseline
.venv/bin/python -m evaluacion.evaluar --sistema multiagente
```

Sistemas disponibles: `baseline` (un solo agente), `multiagente` (cinco reviewers, verificador y sintetizador) y las ablaciones `sin_verificador` y `sin_rag`.

Los resultados crudos quedan en `resultados/`: una fila por caso en `resultados_<sistema>.csv`, una fila por sistema en `resumen.csv` y la traza de cada corrida en `trazas/`.

## Frenos

```bash
.venv/bin/python -m evaluacion.forzar_frenos
```

Fuerza los cuatro frenos con un modelo de guion, sin gastar: tope de pasos, presupuesto de tokens, detector de repetición y tiempo máximo de un check. La salida y una traza por freno quedan en `resultados/frenos/`. Los límites se ajustan en `.env` (`REVISOR_MAX_PASOS`, `REVISOR_LIMITE_TOKENS`, `REVISOR_RESERVA_TOKENS`).

## Pruebas

```bash
.venv/bin/python -m pytest -q
```

## Cambiar de proveedor o de repositorio

- **Proveedor:** editar `.env`. Para dar a un solo rol otro modelo, copiar `modelos.toml.example` a `modelos.toml`.
- **Repositorio revisado:** escribir un `perfil.toml` en ese repo con sus comandos de lint, tests y tipos.
