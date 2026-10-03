# Revisor de código multiagente

Sistema en LangGraph que recibe un diff de un repositorio y devuelve un informe de review con hallazgos verificados. Taller 03 de MMIA 6013 IA Generativa y Agentes (USFQ), opción de tema libre.

## Carpetas

- `repo-prueba/`: el repositorio que se revisa. Mini tienda en TypeScript con sus reglas (`CLAUDE.md`) y su perfil (`perfil.toml`).
- `revisor/`: el sistema. Configuración del modelo, estado, herramientas, RAG y traza.
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

## Pruebas

```bash
.venv/bin/python -m pytest -q
```

## Cambiar de proveedor o de repositorio

- **Proveedor:** editar `.env`. Para dar a un solo rol otro modelo, copiar `modelos.toml.example` a `modelos.toml`.
- **Repositorio revisado:** escribir un `perfil.toml` en ese repo con sus comandos de lint, tests y tipos.
