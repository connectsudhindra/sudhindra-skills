"""LLM-based GCCF scorer, run only as a background task after the API has
already responded to the hook (see routers/prompts.py) -- this is a
comparison signal against the heuristic score, never on the blocking path.
"""
from __future__ import annotations

import json
import time

from anthropic import AsyncAnthropic

import config

_SYSTEM_PROMPT = """You score a single prompt a developer sent to a coding agent, on four \
dimensions, each 0-100:

- goal: is there a clear, concrete action and target? ("fix it" scores low; \
"fix the null pointer in UserService.getById" scores high)
- context: does it supply the situational detail the agent can't infer -- \
file paths, error text, when/why this matters?
- constraints: does it bound the scope -- what must stay unchanged, limits, \
requirements?
- format: does it specify the shape of the answer -- a diff, a table, a \
short summary, a specific structure?

Respond with ONLY a JSON object, no prose, no markdown fences: \
{"goal": <0-100>, "context": <0-100>, "constraints": <0-100>, "format": <0-100>, \
"rationale": "<one sentence>"}"""


class LLMScoringError(Exception):
    pass


async def score_prompt(text: str) -> tuple[dict, int]:
    """Returns (scores_dict, latency_ms). Raises LLMScoringError on any failure --
    callers treat this as best-effort and simply skip the llm prompt_scores row."""
    if not config.ANTHROPIC_API_KEY:
        raise LLMScoringError("ANTHROPIC_API_KEY not configured")

    client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    started = time.monotonic()
    try:
        response = await client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=300,
            temperature=0,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text[:4000]}],
        )
    except Exception as exc:  # noqa: BLE001 - any API failure is equally "unusable"
        raise LLMScoringError(str(exc)) from exc

    latency_ms = int((time.monotonic() - started) * 1000)

    raw = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
    try:
        parsed = json.loads(raw)
        for key in ("goal", "context", "constraints", "format"):
            parsed[key] = max(0.0, min(100.0, float(parsed[key])))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise LLMScoringError(f"unparseable model output: {raw!r}") from exc

    return parsed, latency_ms
