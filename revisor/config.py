"""Único lugar donde se decide con qué modelo se habla.

El grafo y los agentes piden su modelo a get_llm(rol) y nunca nombran un
proveedor. Cambiar de la H200 a otro proveedor es editar .env o modelos.toml.
"""

from __future__ import annotations

import json
import os
import tomllib
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")


@dataclass(frozen=True)
class ConfigModelo:
    proveedor: str
    modelo: str
    base_url: str | None
    api_key: str | None


@lru_cache(maxsize=None)
def _modelo_del_endpoint(base_url: str) -> str:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}/models", timeout=15) as respuesta:
        datos = json.load(respuesta)
    return datos["data"][0]["id"]


@lru_cache(maxsize=1)
def _roles() -> dict:
    ruta = RAIZ / "modelos.toml"
    if not ruta.exists():
        return {}
    return tomllib.loads(ruta.read_text(encoding="utf-8")).get("roles", {})


@lru_cache(maxsize=None)
def config_de(rol: str = "default") -> ConfigModelo:
    propio = _roles().get(rol, {})
    proveedor = propio.get("proveedor", os.getenv("LLM_PROVIDER", "openai"))
    if proveedor == "anthropic":
        modelo = propio.get("modelo") or os.getenv("LLM_MODEL") or ""
        if not modelo:
            raise ValueError(f"El rol {rol} usa anthropic y no tiene modelo configurado")
        return ConfigModelo(proveedor, modelo, None, os.getenv("ANTHROPIC_API_KEY"))
    base_url = propio.get("base_url", os.getenv("LLM_BASE_URL", ""))
    if not base_url:
        raise ValueError("Falta LLM_BASE_URL en .env")
    modelo = propio.get("modelo") or os.getenv("LLM_MODEL") or _modelo_del_endpoint(base_url)
    return ConfigModelo(proveedor, modelo, base_url, os.getenv("LLM_API_KEY", "local"))


def id_modelo(rol: str = "default") -> str:
    return config_de(rol).modelo


def get_llm(rol: str = "default"):
    config = config_de(rol)
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    if config.proveedor == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=config.modelo, api_key=config.api_key, max_tokens=max_tokens)
    from langchain_openai import ChatOpenAI

    # El modelo de la H200 razona siempre y lo cobra del cupo de salida: sin
    # acotarlo puede gastar todo en razonar y devolver una respuesta vacía.
    esfuerzo = os.getenv("LLM_REASONING_EFFORT", "")
    extras = {"reasoning_effort": esfuerzo} if esfuerzo else {}
    return ChatOpenAI(
        model=config.modelo,
        base_url=config.base_url,
        api_key=config.api_key,
        max_tokens=max_tokens,
        temperature=0,
        timeout=180,
        **extras,
    )


def estructurado(llm, esquema):
    """Salida con esquema fijo; devuelve {"raw", "parsed", "parsing_error"}. En la
    H200 el método por defecto no le muestra el esquema al modelo; con
    function_calling viaja como herramienta."""
    if type(llm).__name__ == "ChatOpenAI":
        return llm.with_structured_output(esquema, method="function_calling", include_raw=True)
    return llm.with_structured_output(esquema, include_raw=True)


def get_embeddings():
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        base_url=os.getenv("EMBED_BASE_URL"),
        api_key=os.getenv("EMBED_API_KEY", "local"),
        model=os.getenv("EMBED_MODEL", "bge-m3:latest"),
        check_embedding_ctx_length=False,
    )
