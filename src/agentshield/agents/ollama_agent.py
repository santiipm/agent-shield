"""Ollama-backed agent that calls a local Ollama server via HTTP."""

import os
import time

import httpx

from agentshield.logging_config import get_logger

logger = get_logger(__name__)


class OllamaAgent:
    """Agent that sends prompts to a local Ollama server and returns responses."""

    def __init__(self, model: str, base_url: str | None = None) -> None:
        self._model = model
        self._base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self._client = httpx.AsyncClient(timeout=60.0)

    async def invoke(self, message: str) -> str:
        """POST the prompt to Ollama and return the generated text."""
        url = f"{self._base_url}/api/generate"
        payload = {"model": self._model, "prompt": message, "stream": False}

        logger.info("ollama_request_started", model=self._model)
        request_start = time.monotonic()

        response = await self._client.post(url, json=payload)
        response.raise_for_status()

        duration = time.monotonic() - request_start
        logger.info(
            "ollama_request_completed",
            model=self._model,
            duration_seconds=duration,
        )

        data = response.json()
        return str(data["response"])
