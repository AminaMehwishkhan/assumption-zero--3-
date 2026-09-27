"""
AI Mode

Assumption Zero runs entirely in DEMO MODE by default: the regex-based
POLICY.md parser in requirements.py, and every agent in analyzer/agents/,
are deterministic and require no external API. This guarantees the
hackathon demo can never collapse because a third-party API is slow,
rate-limited, or unavailable.

AI MODE is optional and additive. If ANTHROPIC_API_KEY is set in the
environment, this module can interpret an arbitrary, unstructured policy
document (one that doesn't use the `### REQ-n` heading convention our
bundled POLICY.md uses) into the same structured requirement schema. This
is what lets Assumption Zero generalize to a policy document or repository
it wasn't specifically built around.

Every function here fails closed: on a missing key, network error, bad
response, or malformed JSON, it returns None and the caller (see
requirements.py::extract_requirements) falls back to demo mode. Nothing in
this module ever raises out to the caller.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

# Any current Anthropic model works here; this is the general-purpose
# model current as of this build. Swap freely for whatever your API key
# and tier support.
AI_MODEL = "claude-sonnet-5"
API_URL = "https://api.anthropic.com/v1/messages"
REQUEST_TIMEOUT_SECONDS = 20

EXTRACTION_SYSTEM_PROMPT = """You extract binding human-eligibility requirements from a software policy document.

Read the policy text and identify every requirement that describes who the software MUST support (e.g. people without certain information, people using certain formats, people in certain situations).

Respond with ONLY a JSON array (no prose, no markdown fences) of objects shaped exactly like:
[{"id": "REQ-1", "title": "short title", "statement": "the binding requirement in one or two sentences", "keywords": ["keyword1", "keyword2"]}]

Number requirements REQ-1, REQ-2, etc. in the order they appear. If the document has no such requirements, respond with an empty JSON array: []"""


def is_enabled() -> bool:
    """AI mode is enabled purely by the presence of an API key. No other
    configuration is required, and nothing else in Assumption Zero
    depends on this being true -- demo mode works identically either way."""
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def extract_requirements_ai(policy_text: str) -> list[dict[str, Any]] | None:
    """Attempt to extract structured requirements from an arbitrary policy
    document using the Anthropic API. Returns None on any failure so the
    caller can fall back to demo mode -- this function is intentionally
    unable to raise or crash its caller.
    """
    if not is_enabled():
        return None

    try:
        import httpx
    except ImportError:
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        response = httpx.post(
            API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": AI_MODEL,
                "max_tokens": 1500,
                "system": EXTRACTION_SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": policy_text[:12000]}
                ],
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        text_blocks = [
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        raw_text = "\n".join(text_blocks).strip()

        # Models sometimes wrap JSON in a markdown fence despite
        # instructions not to -- strip it defensively.
        raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip())

        parsed = json.loads(raw_text)
        if not isinstance(parsed, list):
            return None

        # Validate shape before handing back to the caller; any malformed
        # entry invalidates the whole batch rather than silently
        # corrupting downstream requirement objects.
        for item in parsed:
            if not all(k in item for k in ("id", "title", "statement")):
                return None
            item.setdefault("keywords", [])

        return parsed

    except Exception:
        # Network error, timeout, non-2xx response, malformed JSON,
        # unexpected shape -- all treated the same: fall back to demo mode.
        return None
