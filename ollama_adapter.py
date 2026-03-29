"""
Ollama adapter — drop-in replacement for OpenAI calls in PropSwift.

Provides the same interface as the OpenAI Python SDK but uses Ollama's native
API internally. This gives full control over parameters like `think` that the
OpenAI-compatible endpoint doesn't support.

Usage in openai_service.py:

    # Before (OpenAI)
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[...],
        temperature=0,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content

    # After (local LLM via this adapter)
    from ollama_adapter import OllamaClient
    client = OllamaClient(base_url="http://localhost:11434")
    response = client.chat.completions.create(
        model="qwen3:14b",
        messages=[...],
        temperature=0,
        response_format={"type": "json_object"},  # or json_schema
        think=False,  # extra param: control thinking mode
    )
    content = response.choices[0].message.content
"""

import json
import time
import requests
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Response objects — mimic OpenAI SDK structure
# ---------------------------------------------------------------------------
@dataclass
class Message:
    role: str
    content: str
    reasoning: str | None = None


@dataclass
class Choice:
    index: int
    message: Message
    finish_reason: str


@dataclass
class Usage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class ChatCompletion:
    id: str
    model: str
    choices: list[Choice]
    usage: Usage
    created: int = 0
    object: str = "chat.completion"


# ---------------------------------------------------------------------------
# Completions namespace — mimics client.chat.completions
# ---------------------------------------------------------------------------
class Completions:
    def __init__(self, base_url: str, default_timeout: int):
        self._base_url = base_url.rstrip("/")
        self._default_timeout = default_timeout

    def create(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
        think: bool = False,
        timeout: int | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """
        Create a chat completion using Ollama's native API.

        Supports OpenAI-style response_format and converts it to Ollama's
        format parameter internally.

        Parameters
        ----------
        model : str
            Ollama model name (e.g. "qwen3:14b")
        messages : list[dict]
            Chat messages in OpenAI format
        temperature : float
            Sampling temperature
        max_tokens : int
            Maximum tokens to generate
        response_format : dict | None
            OpenAI-style response format. Supported types:
            - {"type": "json_object"} → Ollama format: "json"
            - {"type": "json_schema", "json_schema": {"schema": {...}}} → Ollama format: schema dict
        think : bool
            Whether to enable thinking mode (default False).
            Use True for complex reasoning tasks (e.g. ranking).
            Use False for simple tasks (e.g. classification).
        timeout : int | None
            Request timeout in seconds
        """
        # Convert OpenAI response_format to Ollama format parameter
        ollama_format = None
        if response_format:
            fmt_type = response_format.get("type")
            if fmt_type == "json_object":
                ollama_format = "json"
            elif fmt_type == "json_schema":
                # OpenAI wraps schema in json_schema.schema
                schema = response_format.get("json_schema", {}).get("schema")
                if schema:
                    ollama_format = schema
            elif isinstance(response_format, dict) and "type" in response_format:
                # Already an Ollama-native schema dict (has "type": "object")
                if response_format.get("type") == "object":
                    ollama_format = response_format

        # Build Ollama native API payload
        payload = {
            "model": model,
            "messages": messages,
            "think": think,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if ollama_format:
            payload["format"] = ollama_format

        req_timeout = timeout or self._default_timeout

        resp = requests.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=req_timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract response data
        msg_data = data.get("message", {})
        content = msg_data.get("content", "")
        thinking = msg_data.get("thinking")

        # Build token usage from Ollama response
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

        return ChatCompletion(
            id=f"chatcmpl-ollama-{int(time.time())}",
            model=data.get("model", model),
            choices=[
                Choice(
                    index=0,
                    message=Message(
                        role=msg_data.get("role", "assistant"),
                        content=content,
                        reasoning=thinking,
                    ),
                    finish_reason=data.get("done_reason", "stop"),
                )
            ],
            usage=Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            created=int(time.time()),
        )


# ---------------------------------------------------------------------------
# Chat namespace — mimics client.chat
# ---------------------------------------------------------------------------
class Chat:
    def __init__(self, base_url: str, default_timeout: int):
        self.completions = Completions(base_url, default_timeout)


# ---------------------------------------------------------------------------
# Main client — mimics OpenAI() client
# ---------------------------------------------------------------------------
class OllamaClient:
    """
    Drop-in replacement for OpenAI client that uses Ollama's native API.

    Example:
        client = OllamaClient(base_url="http://localhost:11434")
        response = client.chat.completions.create(
            model="qwen3:14b",
            messages=[{"role": "user", "content": "Hello"}],
            think=False,
        )
        print(response.choices[0].message.content)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        api_key: str | None = None,  # accepted but ignored (OpenAI compat)
        default_timeout: int = 120,
    ):
        self._base_url = base_url.rstrip("/")
        self.chat = Chat(self._base_url, default_timeout)

    def is_available(self) -> bool:
        """Check if Ollama is running and reachable."""
        try:
            r = requests.get(f"{self._base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except requests.ConnectionError:
            return False

    def list_models(self) -> list[str]:
        """List available models."""
        try:
            r = requests.get(f"{self._base_url}/api/tags", timeout=5)
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Factory function — choose OpenAI or Ollama based on config
# ---------------------------------------------------------------------------
def create_llm_client(
    use_local: bool = False,
    local_base_url: str = "http://localhost:11434",
    openai_api_key: str | None = None,
):
    """
    Factory that returns either an OllamaClient or an OpenAI client.

    Usage in settings/config:
        client = create_llm_client(
            use_local=settings.USE_LOCAL_LLM,
            local_base_url=settings.LOCAL_LLM_BASE_URL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

    The returned client has the same .chat.completions.create() interface
    regardless of which backend is used.
    """
    if use_local:
        return OllamaClient(base_url=local_base_url)
    else:
        from openai import OpenAI
        return OpenAI(api_key=openai_api_key)
