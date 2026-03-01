"""Ollama HTTP client for chat/generate. Uses standard library only."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 120


class OllamaError(Exception):
    """Raised when Ollama request fails."""

    pass


def _request(
    base_url: str,
    path: str,
    body: dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            msg = err_json.get("error", err_body)
        except Exception:
            msg = str(e)
        raise OllamaError(f"Ollama HTTP {e.code}: {msg}") from e
    except urllib.error.URLError as e:
        raise OllamaError(f"Ollama connection failed: {e.reason}") from e
    except TimeoutError as e:
        raise OllamaError(f"Ollama request timed out after {timeout}s") from e


def chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int = DEFAULT_TIMEOUT,
    dry_run: bool = False,
    dry_run_response: str = "",
) -> str:
    """
    Send chat completion request. Tries /api/chat first; falls back to /api/generate
    if needed. Returns the assistant message content.
    """
    if dry_run:
        return dry_run_response or "(dry-run: no LLM response)"

    body = {"model": model, "messages": messages, "stream": False}

    # Prefer /api/chat (stream: false returns full response)
    try:
        out = _request(base_url, "/api/chat", body, timeout=timeout)
    except OllamaError as err:
        err_str = str(err).lower()
        if "404" in err_str or "not found" in err_str:
            # Fallback: /api/generate with prompt built from messages
            prompt = _messages_to_prompt(messages)
            gen_body = {"model": model, "prompt": prompt, "stream": False}
            out = _request(base_url, "/api/generate", gen_body, timeout=timeout)
            return out.get("response", "").strip()
        raise

    # /api/chat response: message.content
    msg = out.get("message") or {}
    return (msg.get("content") or "").strip()


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        else:
            parts.append(f"Assistant: {content}")
    parts.append("Assistant:")
    return "\n\n".join(parts)
