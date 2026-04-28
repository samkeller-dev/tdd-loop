"""Minimal Ollama HTTP client with format=json constrained output."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

import httpx

from .schemas import AttemptOutput

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "mistral:7b-instruct"


class LLMClient(Protocol):
    """Protocol so the loop can be unit-tested with a fake."""

    def generate(self, prompt: str) -> AttemptOutput: ...


@dataclass
class OllamaClient:
    """Talks to a local Ollama server via /api/generate with format=json."""

    model: str = DEFAULT_MODEL
    host: str = DEFAULT_HOST
    # 6 min: covers slow CPU-only Mistral 7B generations, including the
    # longer refine prompts that include prior code + traceback.
    timeout_s: float = 360.0
    # Slight randomness across retries lets the model escape "stuck" wrong
    # answers when the refine prompt alone doesn't budge it. Higher than
    # typical code-completion temperatures because the refine signal is
    # already strong enough that we want diversity, not determinism.
    temperature: float = 0.6

    def generate(self, prompt: str) -> AttemptOutput:
        # Ollama supports format="json" for guaranteed-parseable JSON output.
        # We additionally include the schema in the prompt so the model knows
        # which fields to emit.
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": self.temperature},
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            resp = client.post(f"{self.host}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        raw = data.get("response", "")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Ollama returned non-JSON despite format=json: {raw[:500]!r}"
            ) from exc
        if isinstance(parsed, dict) and isinstance(parsed.get("code"), str):
            parsed["code"] = _strip_markdown_fence(parsed["code"])
        return AttemptOutput.model_validate(parsed)


def _strip_markdown_fence(code: str) -> str:
    """Some models wrap code in ```python ... ``` despite the prompt.

    Strip a leading fence (with or without language tag) and the matching
    trailing fence so the runner doesn't choke on a SyntaxError.
    """
    s = code.strip()
    if not s.startswith("```"):
        return code
    # Drop the opening fence line (```python or ```).
    first_nl = s.find("\n")
    if first_nl == -1:
        return code
    body = s[first_nl + 1 :]
    if body.rstrip().endswith("```"):
        body = body.rstrip()[: -len("```")].rstrip()
    return body
