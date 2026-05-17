"""Capa de proveedores LLM.

Tres implementaciones concretas:

  * `AnthropicProvider` — modelos Claude vía SDK oficial (claude-*).
  * `OpenAIProvider`    — modelos GPT vía SDK oficial (gpt-*, o1*).
  * `OllamaProvider`    — modelos abiertos locales vía API HTTP de Ollama.
                          No requiere clave; ideal para corridas offline.

Todas implementan la misma interfaz `LLMProvider.complete()` y devuelven un
`ModelResponse` uniforme con texto, tokens y latencia. La factoría
`build_provider()` selecciona la implementación por prefijo del modelo.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod

from omb.models import ModelResponse


# ---------------------------------------------------------------------------
# Interfaz
# ---------------------------------------------------------------------------

class LLMProvider(ABC):
    name: str

    @abstractmethod
    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ModelResponse:
        """Envía `prompt` al modelo y devuelve la respuesta envuelta."""


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Falta el paquete 'anthropic'. Instálalo con `pip install -e .`."
            ) from exc

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY no está definida. Revisa tu .env."
            )

        self.name = model
        self._client = Anthropic(api_key=key)

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ModelResponse:
        kwargs: dict = {
            "model": self.name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        t0 = time.perf_counter()
        message = self._client.messages.create(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text = "".join(
            b.text for b in message.content if getattr(b, "type", None) == "text"
        )
        return ModelResponse(
            model=self.name,
            text=text,
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# OpenAI (GPT / o-series)
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """Adaptador para la Chat Completions API de OpenAI."""

    def __init__(self, model: str, api_key: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "Falta el paquete 'openai'. Instálalo con `pip install -e .`."
            ) from exc

        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY no está definida. Revisa tu .env."
            )

        self.name = model
        self._client = OpenAI(api_key=key)
        # Modelos o-series no aceptan temperature.
        self._supports_temperature = not model.startswith(("o1", "o3", "o4"))

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ModelResponse:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict = {
            "model": self.name,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if self._supports_temperature:
            kwargs["temperature"] = temperature

        t0 = time.perf_counter()
        response = self._client.chat.completions.create(**kwargs)
        latency_ms = int((time.perf_counter() - t0) * 1000)

        text = response.choices[0].message.content or ""
        usage = response.usage
        return ModelResponse(
            model=self.name,
            text=text,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# Ollama (local, sin clave)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Adaptador para Ollama corriendo localmente.

    Por defecto apunta a http://localhost:11434/api/chat. El prefijo
    'ollama:' se elimina del nombre del modelo antes de enviarlo
    (p. ej. `ollama:llama3.1:8b` → `llama3.1:8b`).
    """

    def __init__(self, model: str, base_url: str | None = None) -> None:
        try:
            import httpx  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "Falta el paquete 'httpx'. Instálalo con `pip install -e .`."
            ) from exc

        # Normalizar nombre: aceptamos 'ollama:xxx' o 'xxx'.
        self.name = model.removeprefix("ollama:") if model.startswith("ollama:") else model
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL")
            or "http://localhost:11434"
        ).rstrip("/")

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> ModelResponse:
        import httpx

        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        t0 = time.perf_counter()
        with httpx.Client(timeout=600.0) as client:
            response = client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        latency_ms = int((time.perf_counter() - t0) * 1000)

        return ModelResponse(
            model=self.name,
            text=data.get("message", {}).get("content", ""),
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
            latency_ms=latency_ms,
        )


# ---------------------------------------------------------------------------
# Factoría
# ---------------------------------------------------------------------------

def build_provider(model: str) -> LLMProvider:
    """Selecciona el proveedor por prefijo del nombre del modelo.

    Convenciones:
      * `claude*`     → AnthropicProvider
      * `gpt*`, `o1*`, `o3*`, `o4*` → OpenAIProvider
      * `ollama:*`    → OllamaProvider (prefijo explícito)

    Si necesitas un modelo de Ollama sin prefijo (p. ej. para corridas
    100 % locales) puedes inyectar `OllamaProvider(model)` directamente.
    """
    if model.startswith("claude"):
        return AnthropicProvider(model)
    if model.startswith(("gpt", "o1", "o3", "o4")):
        return OpenAIProvider(model)
    if model.startswith("ollama:"):
        return OllamaProvider(model)
    raise ValueError(
        f"Modelo '{model}' no soportado. Usa prefijo 'claude*', 'gpt*', "
        f"'o1*'/'o3*'/'o4*' o 'ollama:<nombre>'."
    )
