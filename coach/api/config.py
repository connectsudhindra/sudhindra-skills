"""Process-wide settings, read once from the environment at import time.

Kept as a plain module rather than a class hierarchy -- there's one process,
one environment, no per-request variation, so a settings object would just
be ceremony around `os.environ.get`.
"""
from __future__ import annotations

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://coach:coach_dev_only@localhost:5433/coach"
)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.environ.get("COACH_LLM_MODEL", "claude-haiku-4-5-20251001")

# When set, write endpoints require a matching `X-Coach-Token` header. Empty
# (the default) means no auth -- fine for a trusted-network pilot, not fine
# for anything exposed publicly.
API_TOKEN = os.environ.get("COACH_API_TOKEN", "")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Leveling policy -- see services/level_engine.py for how these are used.
ROLLING_WINDOW_SIZE = int(os.environ.get("COACH_ROLLING_WINDOW", "20"))
MIN_SCORABLE_PROMPTS_TO_LEVEL = int(os.environ.get("COACH_MIN_PROMPTS_TO_LEVEL", "5"))

# How long a session can go without a new prompt before the sweep closes it
# out, for sessions whose SessionEnd hook never fired (crash, force-quit).
STALE_SESSION_MINUTES = int(os.environ.get("COACH_STALE_SESSION_MINUTES", "20"))
SWEEP_INTERVAL_SECONDS = int(os.environ.get("COACH_SWEEP_INTERVAL_SECONDS", "300"))
