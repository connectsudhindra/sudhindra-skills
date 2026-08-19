"""Tiny stdlib-only HTTP client for talking to the coach API from a hook.
Deliberately not `requests`/`httpx` -- hook scripts must run with nothing
more than a system python3, no venv, no pip install step, so anything here
has to work with only the standard library.

Every function in this module swallows its own exceptions and returns None
on failure, logging to coach/logs/hook.log for troubleshooting -- never to
stdout/stderr on this path, since stderr is how UserPromptSubmit shows a
block reason to the user, and an unrelated network error must never be
mistaken for that.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "hook.log"


def _logger() -> logging.Logger:
    logger = logging.getLogger("coach.hook")
    if not logger.handlers:
        try:
            _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(_LOG_PATH)
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        except OSError:
            logger.addHandler(logging.NullHandler())
    return logger


def post_json(
    url: str, body: dict[str, Any], token: str | None = None, timeout: float = 2.0
) -> dict | None:
    """POST body as JSON, return the parsed response or None on any failure.
    `timeout` covers the whole request (connect + read) -- urllib doesn't
    split the two, so this is intentionally a little tighter than a
    connect/read split would allow, trading a bit of patience for a hard
    upper bound on hook wall-clock time."""
    data = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Coach-Token"] = token

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - network failure is a single case here
        _logger().info("POST %s failed: %s", url, exc)
        return None


def get_json(url: str, timeout: float = 1.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        _logger().info("GET %s failed: %s", url, exc)
        return None
