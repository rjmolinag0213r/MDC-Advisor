"""OpenAI-compatible LLM provider chain.

Providers are tried in the order given by LLM_PROVIDERS (default: prune,gemini,openrouter).
A provider is skipped when its API key is not set, so the app still runs with any subset
of keys, or with none (callers then fall back to the offline engine).

- prune:      Prune gateway (https://withprune.com) in front of the model. One base-URL change.
- gemini:     Google Gemini through its OpenAI-compatible endpoint.
- openrouter: OpenRouter, defaulting to a Gemini model.
"""
from __future__ import annotations

import base64
import os
import threading
from dataclasses import dataclass

import requests
from openai import OpenAI


@dataclass
class Provider:
    name: str
    base_url: str
    key_env: str
    model_env: str
    default_model: str

    @property
    def api_key(self) -> str | None:
        key = os.getenv(self.key_env, "").strip()
        return key or None

    @property
    def model(self) -> str:
        return os.getenv(self.model_env, "").strip() or self.default_model


PROVIDERS = {
    # Prune is not OpenAI-compatible: X-Prune-Key header + one proxy route per upstream provider.
    # The upstream key (e.g. Gemini) lives in the Prune vault (dashboard: Connect -> Providers).
    "prune": Provider("prune", os.getenv("PRUNE_BASE_URL", "https://api.withprune.com").rstrip("/").removesuffix("/v1"),
                      "PRUNE_API_KEY", "PRUNE_MODEL", "gemini-flash-lite-latest"),
    "gemini": Provider("gemini", "https://generativelanguage.googleapis.com/v1beta/openai/",
                       "GEMINI_API_KEY", "GEMINI_MODEL", "gemini-flash-lite-latest"),
    "openrouter": Provider("openrouter", "https://openrouter.ai/api/v1",
                           "OPENROUTER_API_KEY", "OPENROUTER_MODEL", "google/gemini-2.5-flash"),
}


def provider_order() -> list[Provider]:
    names = os.getenv("LLM_PROVIDERS", "prune,gemini,openrouter").split(",")
    return [PROVIDERS[n.strip()] for n in names if n.strip() in PROVIDERS]


def available_providers() -> list[str]:
    return [p.name for p in provider_order() if p.api_key]


class LLMUnavailable(Exception):
    pass


PRUNE_ROUTES = {
    "gemini": "/v1/proxy/gemini/generateContent",
    "openrouter": "/v1/proxy/openrouter/chat/completions",
    "openai": "/v1/proxy/openai/chat/completions",
}


def _prune_text(data: dict) -> str:
    """Accept OpenAI-style or Gemini-native response bodies."""
    if data.get("choices"):
        return data["choices"][0].get("message", {}).get("content") or ""
    for cand in data.get("candidates") or []:
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        if text:
            return text
    return data.get("text") or data.get("content") or ""


def prune_summary(meta: dict | None) -> dict | None:
    """The Prune fields worth showing a judge: cache hit, tokens and dollars saved, what it applied."""
    if not isinstance(meta, dict):
        return None
    return {
        "cacheHit": bool(meta.get("cache_hit")),
        "cacheType": meta.get("cache_type"),
        "tokensSaved": meta.get("tokens_saved") or 0,
        "originalTokens": meta.get("original_tokens"),
        "costWithoutPruneUsd": meta.get("cost_without_prune_usd"),
        "costWithPruneUsd": meta.get("cost_with_prune_usd"),
        "costSavedUsd": meta.get("cost_saved_usd", meta.get("cost_saved")) or 0,
        "optimizations": [o for o in (meta.get("optimizations_applied") or []) if ":" not in o][:6],
        "provider": meta.get("provider"),
    }


class _Savings:
    """Running totals of what Prune saved since the server started (for /api/stats)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.calls = self.cache_hits = self.tokens = 0
        self.usd = self.usd_without = 0.0

    def add(self, s: dict | None):
        if not s:
            return
        with self.lock:
            self.calls += 1
            self.cache_hits += int(s["cacheHit"])
            self.tokens += int(s["tokensSaved"] or 0)
            self.usd += float(s["costSavedUsd"] or 0)
            self.usd_without += float(s["costWithoutPruneUsd"] or 0)

    def snapshot(self) -> dict:
        with self.lock:
            return {"pruneCalls": self.calls, "cacheHits": self.cache_hits,
                    "cacheHitRate": round(self.cache_hits / self.calls, 3) if self.calls else 0.0,
                    "tokensSaved": self.tokens, "costSavedUsd": round(self.usd, 6),
                    "costWithoutPruneUsd": round(self.usd_without, 6)}


SAVINGS = _Savings()


def _complete_prune(p: Provider, messages: list[dict], temperature: float, max_tokens: int, timeout: float,
                    meta_out: dict | None = None) -> str:
    upstream = os.getenv("PRUNE_UPSTREAM", "gemini").strip()
    route = PRUNE_ROUTES.get(upstream, PRUNE_ROUTES["gemini"])
    body = {"messages": messages, "model": p.model, "max_tokens": max_tokens, "temperature": temperature}
    r = requests.post(p.base_url + route, headers={"X-Prune-Key": p.api_key, "Content-Type": "application/json"},
                      json=body, timeout=timeout)
    if r.status_code >= 400:
        try:
            err = r.json()
            msg = f"{err.get('error')} {err.get('upstream_error_snippet') or ''}".strip()
        except ValueError:
            msg = r.text[:200]
        raise RuntimeError(f"HTTP {r.status_code}: {msg[:240]}")
    data = r.json()
    summary = prune_summary(data.get("prune_metadata"))
    if summary:
        summary["latencyMs"] = r.headers.get("x-prune-total-ms")
        SAVINGS.add(summary)
        if meta_out is not None:
            meta_out["prune"] = summary
    return _prune_text(data)


def complete(messages: list[dict], *, json_mode: bool = True, temperature: float = 0.5,
             max_tokens: int = 1200, timeout: float = 25, budget: float | None = None,
             meta_out: dict | None = None) -> tuple[str, str]:
    """Return (content, "provider/model"). Raises LLMUnavailable if every provider fails.

    budget caps the TOTAL seconds spent across the whole fallback chain (default LLM_BUDGET_SECONDS
    or 30), so a caller never waits for three full timeouts back to back.
    """
    import time
    budget = budget if budget is not None else float(os.getenv("LLM_BUDGET_SECONDS", "30"))
    deadline = time.monotonic() + budget
    errors = []
    for p in provider_order():
        if not p.api_key:
            continue
        remaining = deadline - time.monotonic()
        if remaining < 3:
            errors.append(f"{p.name}: skipped, time budget used up")
            break
        timeout = min(timeout, remaining)
        if p.name == "prune":
            try:
                content = _complete_prune(p, messages, temperature, max_tokens, timeout, meta_out)
                if content.strip():
                    return content, f"prune/{p.model}"
                errors.append("prune: empty response")
            except Exception as e:
                errors.append(f"prune: {str(e)[:200]}")
                print(f"[llm] prune failed: {str(e)[:240]}")
            continue
        try:
            client = OpenAI(base_url=p.base_url, api_key=p.api_key, timeout=timeout, max_retries=1)
            kwargs = dict(model=p.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            content = resp.choices[0].message.content or ""
            if content.strip():
                return content, f"{p.name}/{p.model}"
            errors.append(f"{p.name}: empty response")
        except Exception as e:  # try the next provider
            errors.append(f"{p.name}: {type(e).__name__}: {str(e)[:160]}")
            print(f"[llm] {p.name} failed: {type(e).__name__}: {str(e)[:200]}")
    raise LLMUnavailable("; ".join(errors) or "no LLM provider configured")


def gemini_vision(prompt: str, data: bytes, mime: str, *, timeout: float = 45) -> tuple[str, str]:
    """Send an image or PDF to Gemini directly (native multimodal; Prune's proxy is text-only).

    Returns (text, "gemini/model"). Raises LLMUnavailable when no Gemini key or the call fails.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise LLMUnavailable("GEMINI_API_KEY not set")
    model = os.getenv("GEMINI_VISION_MODEL", "").strip() or PROVIDERS["gemini"].model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "contents": [{"parts": [{"text": prompt},
                                {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1},
    }
    try:
        r = requests.post(url, headers={"x-goog-api-key": key}, json=body, timeout=timeout)
    except requests.RequestException as e:
        raise LLMUnavailable(f"gemini vision: {type(e).__name__}") from e
    if r.status_code >= 400:
        raise LLMUnavailable(f"gemini vision HTTP {r.status_code}: {r.text[:200]}")
    return _prune_text(r.json()), f"gemini/{model}"
