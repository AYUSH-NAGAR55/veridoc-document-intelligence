"""Thin HTTP client for a locally-running Ollama server.

This makes real HTTP calls to OLLAMA_URL — there is no mock or stub path
here. If Ollama isn't running, `generate_json` raises `OllamaUnavailable`,
which the extraction layer catches and turns into a clear, non-crashing
document status rather than a stack trace.
"""
import json
import urllib.error
import urllib.request

from .. import config


class OllamaUnavailable(Exception):
    pass


class OllamaMalformedResponse(Exception):
    pass


def generate_json(prompt: str, system: str = "") -> dict:
    """Call Ollama's /api/generate with format=json, requesting a single
    JSON object back. Raises OllamaUnavailable if the server can't be
    reached at all, or OllamaMalformedResponse if it responds but the
    body isn't valid JSON.
    """
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "format": "json",
        "stream": False,
        "options": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        f"{config.OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.OLLAMA_TIMEOUT_SECONDS) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ConnectionError, TimeoutError) as exc:
        raise OllamaUnavailable(
            f"Couldn't reach Ollama at {config.OLLAMA_URL}. "
            f"Is it running? (`ollama serve`, and `ollama pull {config.OLLAMA_MODEL}`)"
        ) from exc

    raw_text = body.get("response", "")
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise OllamaMalformedResponse(f"Ollama did not return valid JSON: {raw_text[:300]}") from exc


def is_reachable() -> bool:
    try:
        req = urllib.request.Request(f"{config.OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False
