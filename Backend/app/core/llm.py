"""LLM client integration with robust error handling and fallback support.

Supports OpenAI-compatible APIs (OpenAI, Gemini via OpenAI endpoint, Ollama, etc.)
and Gemini REST API.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict | list | None:
    """Extract JSON object or list from text, stripping markdown code fences if present."""
    text = text.strip()
    # Match markdown code block ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try finding outermost { ... } or [ ... ]
        brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                pass
    return None


async def call_llm(
    prompt: str,
    system_prompt: str = "You are OrbitGuard AI, an autonomous spacecraft diagnostics and recovery agent.",
    temperature: float = 0.2,
    timeout: float = 12.0,
) -> str:
    """Call configured LLM provider and return raw text response.

    Raises RuntimeError or httpx.HTTPError if the call fails or no API key is set.
    """
    api_key = settings.LLM_API_KEY
    if not api_key:
        raise RuntimeError("LLM_API_KEY is not configured")

    endpoint = settings.LLM_ENDPOINT.strip()
    model = settings.LLM_MODEL or "gemini-1.5-flash"

    # 1. Gemini REST API endpoint
    if not endpoint or "googleapis.com" in endpoint or "gemini" in model.lower():
        url = endpoint or f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        if "?" not in url and api_key:
            url = f"{url}?key={api_key}"
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"System: {system_prompt}\n\nUser: {prompt}"}
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            raise RuntimeError("Empty response from Gemini API")

    # 2. OpenAI / Compatible Chat Completions API endpoint
    url = endpoint if endpoint else "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def call_llm_structured(
    prompt: str,
    system_prompt: str = "You are OrbitGuard AI. Output valid JSON only.",
    retries: int = 1,
    timeout: float = 12.0,
) -> dict | list:
    """Call LLM with automatic 1-retry on timeout or malformed JSON."""
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            raw_text = await call_llm(prompt, system_prompt=system_prompt, timeout=timeout)
            parsed = _extract_json(raw_text)
            if parsed is not None:
                return parsed
            raise ValueError(f"Malformed JSON from LLM: {raw_text[:200]}")
        except Exception as exc:
            last_error = exc
            logger.warning("LLM call attempt %d failed: %s", attempt + 1, exc)

    raise RuntimeError(f"LLM call failed after {retries + 1} attempts: {last_error}")
